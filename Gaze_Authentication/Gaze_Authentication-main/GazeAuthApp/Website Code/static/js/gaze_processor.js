/**
 * Gaze Processor - Client-side gaze tracking using MediaPipe Face Mesh
 * =====================================================================
 * Real-time eye tracking, blink detection, and feature extraction
 * for Gaze Authentication system.
 */

class GazeProcessor {
    constructor(options = {}) {
        this.options = {
            videoElement: null,
            canvasElement: null,
            onResults: null,
            onError: null,
            showLandmarks: true,
            showGazePoint: true,
            ...options
        };

        // MediaPipe Face Mesh indices
        this.LEFT_EYE = [362, 385, 387, 263, 373, 380];
        this.RIGHT_EYE = [33, 160, 158, 133, 153, 144];
        this.LEFT_IRIS = [474, 475, 476, 477];
        this.RIGHT_IRIS = [469, 470, 471, 472];

        // EAR threshold for blink detection
        this.EAR_THRESHOLD = 0.25;
        this.CONSECUTIVE_FRAMES = 3;

        // Tracking state
        this.isRunning = false;
        this.frameCount = 0;
        this.blinkCount = 0;
        this.blinkFrameCounter = 0;
        this.eyesClosed = false;

        // History for feature extraction
        this.gazeHistory = [];
        this.earHistory = [];
        this.timestampHistory = [];
        this.maxHistorySize = 300; // 10 seconds at 30fps

        // Fixation detection
        this.fixationWindow = [];
        this.fixationTimestamps = [];
        this.fixations = [];
        this.FIXATION_DISPERSION = 50;
        this.FIXATION_DURATION = 0.1;

        // Saccade detection
        this.SACCADE_VELOCITY = 300;
        this.saccades = [];
        this.inSaccade = false;
        this.saccadeStart = null;

        // MediaPipe instances
        this.faceMesh = null;
        this.camera = null;
    }

    async initialize() {
        try {
            // Load MediaPipe Face Mesh
            this.faceMesh = new FaceMesh({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
                }
            });

            this.faceMesh.setOptions({
                maxNumFaces: 1,
                refineLandmarks: true, // Enables iris tracking
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            this.faceMesh.onResults((results) => this.processResults(results));

            // Setup camera
            if (this.options.videoElement) {
                this.camera = new Camera(this.options.videoElement, {
                    onFrame: async () => {
                        if (this.isRunning) {
                            await this.faceMesh.send({ image: this.options.videoElement });
                        }
                    },
                    width: 640,
                    height: 480
                });
            }

            return true;
        } catch (error) {
            console.error('Failed to initialize GazeProcessor:', error);
            if (this.options.onError) {
                this.options.onError(error);
            }
            return false;
        }
    }

    async start() {
        if (!this.faceMesh) {
            await this.initialize();
        }

        this.isRunning = true;
        this.frameCount = 0;
        this.resetHistory();

        if (this.camera) {
            await this.camera.start();
        }
    }

    stop() {
        this.isRunning = false;
        if (this.camera) {
            this.camera.stop();
        }
    }

    processResults(results) {
        const timestamp = performance.now() / 1000;
        this.frameCount++;

        const data = {
            faceDetected: false,
            leftEye: null,
            rightEye: null,
            leftIris: null,
            rightIris: null,
            leftPupil: null,
            rightPupil: null,
            gazeRatio: null,
            verticalRatio: null,
            gazePoint: null,
            earLeft: null,
            earRight: null,
            earAverage: null,
            blinkDetected: false,
            totalBlinks: this.blinkCount,
            fixation: null,
            saccade: null,
            timestamp: timestamp,
            frameCount: this.frameCount
        };

        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            const landmarks = results.multiFaceLandmarks[0];
            data.faceDetected = true;

            // Extract eye landmarks
            const videoWidth = this.options.videoElement.videoWidth;
            const videoHeight = this.options.videoElement.videoHeight;

            data.leftEye = this.LEFT_EYE.map(idx => ({
                x: landmarks[idx].x * videoWidth,
                y: landmarks[idx].y * videoHeight
            }));

            data.rightEye = this.RIGHT_EYE.map(idx => ({
                x: landmarks[idx].x * videoWidth,
                y: landmarks[idx].y * videoHeight
            }));

            data.leftIris = this.LEFT_IRIS.map(idx => ({
                x: landmarks[idx].x * videoWidth,
                y: landmarks[idx].y * videoHeight
            }));

            data.rightIris = this.RIGHT_IRIS.map(idx => ({
                x: landmarks[idx].x * videoWidth,
                y: landmarks[idx].y * videoHeight
            }));

            // Calculate pupil centers
            data.leftPupil = this.calculateCentroid(data.leftIris);
            data.rightPupil = this.calculateCentroid(data.rightIris);

            // Calculate EAR for blink detection
            data.earLeft = this.calculateEAR(data.leftEye);
            data.earRight = this.calculateEAR(data.rightEye);
            data.earAverage = (data.earLeft + data.earRight) / 2;

            // Detect blinks
            data.blinkDetected = this.detectBlink(data.earAverage, timestamp);
            data.totalBlinks = this.blinkCount;

            // Calculate gaze ratios
            const gazeData = this.calculateGazeRatio(data.leftEye, data.rightEye, data.leftIris, data.rightIris);
            data.gazeRatio = gazeData.horizontal;
            data.verticalRatio = gazeData.vertical;

            // Estimate gaze point on screen
            data.gazePoint = {
                x: (1 - data.gazeRatio) * videoWidth,
                y: data.verticalRatio * videoHeight
            };

            // Update history
            this.updateHistory(data.gazePoint, data.earAverage, timestamp);

            // Detect fixations and saccades
            data.fixation = this.detectFixation(data.gazePoint, timestamp);
            data.saccade = this.detectSaccade(data.gazePoint, timestamp);

            // Draw on canvas if enabled
            if (this.options.canvasElement && this.options.showLandmarks) {
                this.drawOverlay(data);
            }
        }

        // Store EAR history
        if (data.earAverage !== null) {
            this.earHistory.push(data.earAverage);
            if (this.earHistory.length > this.maxHistorySize) {
                this.earHistory.shift();
            }
        }

        // Callback with results
        if (this.options.onResults) {
            this.options.onResults(data);
        }

        return data;
    }

    calculateCentroid(points) {
        if (!points || points.length === 0) return null;
        const sumX = points.reduce((sum, p) => sum + p.x, 0);
        const sumY = points.reduce((sum, p) => sum + p.y, 0);
        return {
            x: sumX / points.length,
            y: sumY / points.length
        };
    }

    calculateEAR(eyePoints) {
        // Eye Aspect Ratio calculation
        // EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        if (!eyePoints || eyePoints.length < 6) return 0.3;

        const p1 = eyePoints[0]; // Outer corner
        const p2 = eyePoints[1]; // Upper outer
        const p3 = eyePoints[2]; // Upper inner
        const p4 = eyePoints[3]; // Inner corner
        const p5 = eyePoints[4]; // Lower inner
        const p6 = eyePoints[5]; // Lower outer

        // Vertical distances
        const v1 = this.distance(p2, p6);
        const v2 = this.distance(p3, p5);

        // Horizontal distance
        const h = this.distance(p1, p4);

        if (h === 0) return 0.3;

        return (v1 + v2) / (2 * h);
    }

    distance(p1, p2) {
        return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
    }

    detectBlink(ear, timestamp) {
        let blinkDetected = false;

        if (ear < this.EAR_THRESHOLD) {
            this.blinkFrameCounter++;
            if (!this.eyesClosed) {
                this.eyesClosed = true;
                this.blinkStartTime = timestamp;
            }
        } else {
            if (this.blinkFrameCounter >= this.CONSECUTIVE_FRAMES) {
                // Blink completed
                this.blinkCount++;
                blinkDetected = true;
            }
            this.blinkFrameCounter = 0;
            this.eyesClosed = false;
        }

        return blinkDetected;
    }

    calculateGazeRatio(leftEye, rightEye, leftIris, rightIris) {
        // Calculate gaze ratio for both eyes
        const leftCenter = this.calculateCentroid(leftEye);
        const leftIrisCenter = this.calculateCentroid(leftIris);
        const rightCenter = this.calculateCentroid(rightEye);
        const rightIrisCenter = this.calculateCentroid(rightIris);

        // Left eye horizontal ratio
        const leftEyeWidth = this.distance(leftEye[0], leftEye[3]);
        const leftEyeHeight = this.distance(leftEye[1], leftEye[4]);
        const leftHRatio = leftEyeWidth > 0 ?
            (leftIrisCenter.x - leftEye[0].x) / leftEyeWidth : 0.5;
        const leftVRatio = leftEyeHeight > 0 ?
            (leftIrisCenter.y - leftEye[1].y) / leftEyeHeight : 0.5;

        // Right eye horizontal ratio
        const rightEyeWidth = this.distance(rightEye[0], rightEye[3]);
        const rightEyeHeight = this.distance(rightEye[1], rightEye[4]);
        const rightHRatio = rightEyeWidth > 0 ?
            (rightIrisCenter.x - rightEye[0].x) / rightEyeWidth : 0.5;
        const rightVRatio = rightEyeHeight > 0 ?
            (rightIrisCenter.y - rightEye[1].y) / rightEyeHeight : 0.5;

        // Average both eyes
        return {
            horizontal: Math.max(0, Math.min(1, (leftHRatio + rightHRatio) / 2)),
            vertical: Math.max(0, Math.min(1, (leftVRatio + rightVRatio) / 2))
        };
    }

    updateHistory(gazePoint, ear, timestamp) {
        this.gazeHistory.push({ ...gazePoint, timestamp });
        this.timestampHistory.push(timestamp);

        if (this.gazeHistory.length > this.maxHistorySize) {
            this.gazeHistory.shift();
            this.timestampHistory.shift();
        }
    }

    detectFixation(gazePoint, timestamp) {
        this.fixationWindow.push(gazePoint);
        this.fixationTimestamps.push(timestamp);

        if (this.fixationWindow.length < 2) return null;

        // Calculate dispersion
        const dispersion = this.calculateDispersion(this.fixationWindow);

        if (dispersion <= this.FIXATION_DISPERSION) {
            // Within threshold - potential fixation
            return null;
        } else {
            // Check if we had a valid fixation
            const duration = this.fixationTimestamps[this.fixationTimestamps.length - 2] -
                            this.fixationTimestamps[0];

            if (duration >= this.FIXATION_DURATION) {
                const fixationPoints = this.fixationWindow.slice(0, -1);
                const centroid = this.calculateCentroid(fixationPoints);

                const fixation = {
                    centroid: centroid,
                    startTime: this.fixationTimestamps[0],
                    endTime: this.fixationTimestamps[this.fixationTimestamps.length - 2],
                    duration: duration,
                    dispersion: this.calculateDispersion(fixationPoints)
                };

                this.fixations.push(fixation);

                // Reset window
                this.fixationWindow = [gazePoint];
                this.fixationTimestamps = [timestamp];

                return fixation;
            }

            // Remove oldest point
            if (this.fixationWindow.length > 2) {
                this.fixationWindow.shift();
                this.fixationTimestamps.shift();
            }
        }

        return null;
    }

    calculateDispersion(points) {
        if (points.length === 0) return 0;

        const xs = points.map(p => p.x);
        const ys = points.map(p => p.y);

        return (Math.max(...xs) - Math.min(...xs)) + (Math.max(...ys) - Math.min(...ys));
    }

    detectSaccade(gazePoint, timestamp) {
        if (this.gazeHistory.length < 2) return null;

        const prev = this.gazeHistory[this.gazeHistory.length - 2];
        const dt = timestamp - prev.timestamp;

        if (dt === 0) return null;

        const dist = this.distance(prev, gazePoint);
        const velocity = dist / dt;

        if (velocity >= this.SACCADE_VELOCITY) {
            if (!this.inSaccade) {
                this.inSaccade = true;
                this.saccadeStart = { point: prev, time: prev.timestamp };
                this.saccadePoints = [prev, gazePoint];
            } else {
                this.saccadePoints.push(gazePoint);
            }
        } else {
            if (this.inSaccade) {
                const duration = timestamp - this.saccadeStart.time;

                if (duration >= 0.02 && duration <= 0.15) {
                    const amplitude = this.distance(this.saccadeStart.point, gazePoint);
                    const direction = Math.atan2(
                        -(gazePoint.y - this.saccadeStart.point.y),
                        gazePoint.x - this.saccadeStart.point.x
                    ) * 180 / Math.PI;

                    const saccade = {
                        startPoint: this.saccadeStart.point,
                        endPoint: gazePoint,
                        startTime: this.saccadeStart.time,
                        endTime: timestamp,
                        duration: duration,
                        amplitude: amplitude,
                        direction: direction,
                        averageVelocity: amplitude / duration
                    };

                    this.saccades.push(saccade);
                    this.inSaccade = false;
                    this.saccadeStart = null;

                    return saccade;
                }

                this.inSaccade = false;
                this.saccadeStart = null;
            }
        }

        return null;
    }

    drawOverlay(data) {
        const canvas = this.options.canvasElement;
        const ctx = canvas.getContext('2d');
        const video = this.options.videoElement;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw eye contours
        if (data.leftEye) {
            this.drawEyeContour(ctx, data.leftEye, '#00ff00');
        }
        if (data.rightEye) {
            this.drawEyeContour(ctx, data.rightEye, '#00ff00');
        }

        // Draw iris
        if (data.leftIris) {
            this.drawIris(ctx, data.leftIris, '#ff00ff');
        }
        if (data.rightIris) {
            this.drawIris(ctx, data.rightIris, '#ff00ff');
        }

        // Draw pupils
        if (data.leftPupil) {
            ctx.beginPath();
            ctx.arc(data.leftPupil.x, data.leftPupil.y, 5, 0, 2 * Math.PI);
            ctx.fillStyle = '#ff0000';
            ctx.fill();
        }
        if (data.rightPupil) {
            ctx.beginPath();
            ctx.arc(data.rightPupil.x, data.rightPupil.y, 5, 0, 2 * Math.PI);
            ctx.fillStyle = '#ff0000';
            ctx.fill();
        }

        // Draw gaze point
        if (this.options.showGazePoint && data.gazePoint) {
            ctx.beginPath();
            ctx.arc(data.gazePoint.x, data.gazePoint.y, 15, 0, 2 * Math.PI);
            ctx.strokeStyle = '#ffff00';
            ctx.lineWidth = 3;
            ctx.stroke();

            // Draw line from center to gaze point
            ctx.beginPath();
            ctx.moveTo(canvas.width / 2, canvas.height / 2);
            ctx.lineTo(data.gazePoint.x, data.gazePoint.y);
            ctx.strokeStyle = 'rgba(255, 255, 0, 0.5)';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        // Draw info
        ctx.fillStyle = '#ffffff';
        ctx.font = '14px Arial';
        ctx.fillText(`Blinks: ${data.totalBlinks}`, 10, 20);
        ctx.fillText(`EAR: ${data.earAverage ? data.earAverage.toFixed(3) : '--'}`, 10, 40);
        ctx.fillText(`Fixations: ${this.fixations.length}`, 10, 60);
        ctx.fillText(`Saccades: ${this.saccades.length}`, 10, 80);
    }

    drawEyeContour(ctx, points, color) {
        if (points.length < 2) return;

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.closePath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    drawIris(ctx, points, color) {
        points.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 2, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
        });
    }

    getFeatures() {
        // Calculate comprehensive features for authentication
        const gazeH = this.gazeHistory.map(g => g.x);
        const gazeV = this.gazeHistory.map(g => g.y);

        const features = {
            // Gaze statistics
            gaze_h_mean: this.mean(gazeH),
            gaze_h_std: this.std(gazeH),
            gaze_v_mean: this.mean(gazeV),
            gaze_v_std: this.std(gazeV),

            // EAR statistics
            ear_mean: this.mean(this.earHistory),
            ear_std: this.std(this.earHistory),
            ear_min: Math.min(...this.earHistory),
            ear_max: Math.max(...this.earHistory),

            // Blink features
            blink_count: this.blinkCount,
            blink_rate: this.calculateBlinkRate(),

            // Fixation features
            fixation_count: this.fixations.length,
            fixation_avg_duration: this.mean(this.fixations.map(f => f.duration)),
            fixation_avg_dispersion: this.mean(this.fixations.map(f => f.dispersion)),

            // Saccade features
            saccade_count: this.saccades.length,
            saccade_avg_amplitude: this.mean(this.saccades.map(s => s.amplitude)),
            saccade_avg_velocity: this.mean(this.saccades.map(s => s.averageVelocity)),
            saccade_avg_duration: this.mean(this.saccades.map(s => s.duration)),

            // Trajectory features
            trajectory_path_length: this.calculatePathLength(),
            trajectory_velocity_mean: this.calculateMeanVelocity(),

            // Session info
            frame_count: this.frameCount,
            duration: this.gazeHistory.length > 0 ?
                this.gazeHistory[this.gazeHistory.length - 1].timestamp - this.gazeHistory[0].timestamp : 0
        };

        return features;
    }

    mean(arr) {
        if (!arr || arr.length === 0) return 0;
        return arr.reduce((a, b) => a + b, 0) / arr.length;
    }

    std(arr) {
        if (!arr || arr.length === 0) return 0;
        const m = this.mean(arr);
        return Math.sqrt(arr.reduce((acc, val) => acc + Math.pow(val - m, 2), 0) / arr.length);
    }

    calculateBlinkRate() {
        if (this.gazeHistory.length < 2) return 0;
        const duration = this.gazeHistory[this.gazeHistory.length - 1].timestamp -
                        this.gazeHistory[0].timestamp;
        if (duration === 0) return 0;
        return (this.blinkCount / duration) * 60; // Blinks per minute
    }

    calculatePathLength() {
        let length = 0;
        for (let i = 1; i < this.gazeHistory.length; i++) {
            length += this.distance(this.gazeHistory[i - 1], this.gazeHistory[i]);
        }
        return length;
    }

    calculateMeanVelocity() {
        if (this.gazeHistory.length < 2) return 0;

        let totalVelocity = 0;
        let count = 0;

        for (let i = 1; i < this.gazeHistory.length; i++) {
            const dt = this.gazeHistory[i].timestamp - this.gazeHistory[i - 1].timestamp;
            if (dt > 0) {
                const dist = this.distance(this.gazeHistory[i - 1], this.gazeHistory[i]);
                totalVelocity += dist / dt;
                count++;
            }
        }

        return count > 0 ? totalVelocity / count : 0;
    }

    resetHistory() {
        this.gazeHistory = [];
        this.earHistory = [];
        this.timestampHistory = [];
        this.fixationWindow = [];
        this.fixationTimestamps = [];
        this.fixations = [];
        this.saccades = [];
        this.blinkCount = 0;
        this.blinkFrameCounter = 0;
        this.eyesClosed = false;
        this.inSaccade = false;
    }

    getStatistics() {
        return {
            totalFrames: this.frameCount,
            totalBlinks: this.blinkCount,
            totalFixations: this.fixations.length,
            totalSaccades: this.saccades.length,
            blinkRate: this.calculateBlinkRate(),
            averageEAR: this.mean(this.earHistory)
        };
    }
}

// Export for use
window.GazeProcessor = GazeProcessor;
