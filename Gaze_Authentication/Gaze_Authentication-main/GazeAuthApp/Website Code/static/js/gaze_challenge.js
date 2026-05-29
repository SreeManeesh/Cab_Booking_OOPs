/**
 * Gaze Challenge - Challenge-Response Authentication
 * ===================================================
 * Implements a secure challenge-response gaze authentication where users
 * must look at specific targets in a specific sequence. This is much more
 * secure than comparing aggregate statistics.
 *
 * The user's unique "gaze signature" comes from:
 * 1. Their personal reaction time to each target
 * 2. The trajectory they take between targets
 * 3. Their fixation accuracy on each target
 * 4. Saccade velocity profiles (unique to each person's oculomotor system)
 */

class GazeChallenge {
    constructor(options = {}) {
        this.options = {
            containerElement: null,
            gazeProcessor: null,
            onComplete: null,
            onProgress: null,
            targetCount: 5,        // Number of targets in sequence
            targetRadius: 40,     // Size of target circles
            targetHoldTime: 0.8,  // Seconds user must fixate on target
            targetTimeout: 5,     // Max seconds per target
            ...options
        };

        // Challenge state
        this.targets = [];
        this.currentTargetIndex = 0;
        this.isRunning = false;

        // Tracking data for signature
        this.challengeData = {
            targetSequence: [],
            gazeTrajectories: [],
            reactionTimes: [],
            fixationAccuracies: [],
            saccadeProfiles: [],
            timestamps: []
        };

        // Current target tracking
        this.targetStartTime = null;
        this.fixationStartTime = null;
        this.currentTrajectory = [];
        this.isFixatingOnTarget = false;
    }

    /**
     * Generate random target positions
     * The SAME sequence is used for enrollment and authentication
     * (stored in user's profile)
     */
    generateTargets(seed = null) {
        const container = this.options.containerElement;
        const width = container.clientWidth;
        const height = container.clientHeight;
        const padding = 60;

        // If seed provided, use deterministic positions
        if (seed) {
            return this.generateSeededTargets(seed, width, height, padding);
        }

        // Generate random positions ensuring good distribution
        const targets = [];
        const gridCols = 3;
        const gridRows = 2;
        const cellWidth = (width - 2 * padding) / gridCols;
        const cellHeight = (height - 2 * padding) / gridRows;

        const positions = [];
        for (let row = 0; row < gridRows; row++) {
            for (let col = 0; col < gridCols; col++) {
                positions.push({
                    x: padding + cellWidth * (col + 0.5) + (Math.random() - 0.5) * cellWidth * 0.5,
                    y: padding + cellHeight * (row + 0.5) + (Math.random() - 0.5) * cellHeight * 0.5
                });
            }
        }

        // Shuffle and pick required number
        this.shuffleArray(positions);
        for (let i = 0; i < this.options.targetCount; i++) {
            targets.push({
                id: i,
                x: positions[i].x,
                y: positions[i].y,
                visited: false
            });
        }

        return targets;
    }

    generateSeededTargets(seed, width, height, padding) {
        // Use seed for reproducible positions (for authentication comparison)
        const random = this.seededRandom(seed);
        const targets = [];

        for (let i = 0; i < this.options.targetCount; i++) {
            targets.push({
                id: i,
                x: padding + random() * (width - 2 * padding),
                y: padding + random() * (height - 2 * padding),
                visited: false
            });
        }

        return targets;
    }

    seededRandom(seed) {
        let s = seed;
        return function() {
            s = Math.sin(s) * 10000;
            return s - Math.floor(s);
        };
    }

    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    /**
     * Start the challenge
     */
    async start(enrolledSequence = null) {
        const container = this.options.containerElement;

        // Generate or use provided targets
        if (enrolledSequence && enrolledSequence.length > 0) {
            this.targets = enrolledSequence.map((t, i) => ({
                id: i,
                x: t.x * container.clientWidth,
                y: t.y * container.clientHeight,
                visited: false
            }));
        } else {
            this.targets = this.generateTargets();
        }

        // Store normalized sequence (0-1 range)
        this.challengeData.targetSequence = this.targets.map(t => ({
            x: t.x / container.clientWidth,
            y: t.y / container.clientHeight
        }));

        // Reset state
        this.currentTargetIndex = 0;
        this.challengeData.gazeTrajectories = [];
        this.challengeData.reactionTimes = [];
        this.challengeData.fixationAccuracies = [];
        this.challengeData.saccadeProfiles = [];
        this.challengeData.timestamps = [];

        // Create visual elements
        this.renderTargets();

        this.isRunning = true;
        this.showTarget(0);

        // Start listening to gaze data
        if (this.options.gazeProcessor) {
            this.options.gazeProcessor.options.onResults = (data) => this.processGazeData(data);
        }
    }

    renderTargets() {
        const container = this.options.containerElement;

        // Clear existing
        container.innerHTML = '';

        // Add targets (hidden initially)
        this.targets.forEach((target, index) => {
            const el = document.createElement('div');
            el.id = `challenge-target-${index}`;
            el.className = 'challenge-target hidden';
            el.style.cssText = `
                position: absolute;
                left: ${target.x - this.options.targetRadius}px;
                top: ${target.y - this.options.targetRadius}px;
                width: ${this.options.targetRadius * 2}px;
                height: ${this.options.targetRadius * 2}px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: 4px solid white;
                box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 24px;
                opacity: 0;
                transform: scale(0);
                transition: all 0.3s ease;
            `;
            el.innerHTML = `<span>${index + 1}</span>`;
            container.appendChild(el);
        });

        // Add progress ring overlay
        const progressRing = document.createElement('div');
        progressRing.id = 'progress-ring';
        progressRing.style.cssText = `
            position: absolute;
            pointer-events: none;
            width: ${this.options.targetRadius * 2 + 20}px;
            height: ${this.options.targetRadius * 2 + 20}px;
            border-radius: 50%;
            border: 4px solid transparent;
            border-top-color: #10b981;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        container.appendChild(progressRing);
    }

    showTarget(index) {
        if (index >= this.targets.length) {
            this.complete();
            return;
        }

        // Hide previous target
        if (index > 0) {
            const prevEl = document.getElementById(`challenge-target-${index - 1}`);
            if (prevEl) {
                prevEl.style.opacity = '0.3';
                prevEl.style.transform = 'scale(0.8)';
                prevEl.style.background = '#10b981';
            }
        }

        // Show current target
        const el = document.getElementById(`challenge-target-${index}`);
        if (el) {
            el.style.opacity = '1';
            el.style.transform = 'scale(1)';
            el.classList.add('pulse');
        }

        this.currentTargetIndex = index;
        this.targetStartTime = performance.now();
        this.fixationStartTime = null;
        this.currentTrajectory = [];
        this.isFixatingOnTarget = false;

        // Report progress
        if (this.options.onProgress) {
            this.options.onProgress({
                current: index + 1,
                total: this.targets.length,
                target: this.targets[index]
            });
        }
    }

    processGazeData(data) {
        if (!this.isRunning || !data.faceDetected || !data.gazePoint) return;

        const currentTarget = this.targets[this.currentTargetIndex];
        const now = performance.now();

        // Store trajectory point
        this.currentTrajectory.push({
            x: data.gazePoint.x,
            y: data.gazePoint.y,
            timestamp: now,
            velocity: this.calculateVelocity(data.gazePoint, now)
        });

        // Calculate distance to target
        const distance = Math.sqrt(
            Math.pow(data.gazePoint.x - currentTarget.x, 2) +
            Math.pow(data.gazePoint.y - currentTarget.y, 2)
        );

        const hitRadius = this.options.targetRadius * 1.5;

        // Update progress ring position
        const ring = document.getElementById('progress-ring');
        if (ring) {
            ring.style.left = `${currentTarget.x - (this.options.targetRadius + 10)}px`;
            ring.style.top = `${currentTarget.y - (this.options.targetRadius + 10)}px`;
        }

        if (distance <= hitRadius) {
            // User is looking at target
            if (!this.isFixatingOnTarget) {
                this.isFixatingOnTarget = true;
                this.fixationStartTime = now;

                // Store reaction time
                const reactionTime = now - this.targetStartTime;
                this.challengeData.reactionTimes.push(reactionTime);
            }

            // Show progress ring
            if (ring) {
                ring.style.opacity = '1';
                const holdProgress = (now - this.fixationStartTime) / (this.options.targetHoldTime * 1000);
                ring.style.transform = `rotate(${holdProgress * 360}deg)`;
            }

            // Check if held long enough
            const holdTime = (now - this.fixationStartTime) / 1000;
            if (holdTime >= this.options.targetHoldTime) {
                // Target completed!
                this.completeTarget();
            }
        } else {
            // User looked away
            if (this.isFixatingOnTarget) {
                this.isFixatingOnTarget = false;
                if (ring) ring.style.opacity = '0';
            }
        }

        // Check timeout
        if ((now - this.targetStartTime) / 1000 > this.options.targetTimeout) {
            // Target timed out - record failure
            this.challengeData.fixationAccuracies.push(0);
            this.challengeData.gazeTrajectories.push(this.normalizeTrajectory(this.currentTrajectory));
            this.showTarget(this.currentTargetIndex + 1);
        }
    }

    calculateVelocity(currentPoint, timestamp) {
        if (this.currentTrajectory.length < 1) return 0;

        const prev = this.currentTrajectory[this.currentTrajectory.length - 1];
        const dt = (timestamp - prev.timestamp) / 1000;
        if (dt === 0) return 0;

        const distance = Math.sqrt(
            Math.pow(currentPoint.x - prev.x, 2) +
            Math.pow(currentPoint.y - prev.y, 2)
        );

        return distance / dt;
    }

    completeTarget() {
        const currentTarget = this.targets[this.currentTargetIndex];

        // Calculate fixation accuracy (how close to center)
        const lastPoints = this.currentTrajectory.slice(-10);
        const avgX = lastPoints.reduce((s, p) => s + p.x, 0) / lastPoints.length;
        const avgY = lastPoints.reduce((s, p) => s + p.y, 0) / lastPoints.length;
        const accuracy = 1 - Math.min(1, Math.sqrt(
            Math.pow(avgX - currentTarget.x, 2) +
            Math.pow(avgY - currentTarget.y, 2)
        ) / this.options.targetRadius);

        this.challengeData.fixationAccuracies.push(accuracy);

        // Store normalized trajectory
        this.challengeData.gazeTrajectories.push(this.normalizeTrajectory(this.currentTrajectory));

        // Extract saccade profile (velocity curve)
        this.challengeData.saccadeProfiles.push(this.extractSaccadeProfile());

        // Mark target as visited
        this.targets[this.currentTargetIndex].visited = true;

        // Hide progress ring
        const ring = document.getElementById('progress-ring');
        if (ring) ring.style.opacity = '0';

        // Move to next target
        this.showTarget(this.currentTargetIndex + 1);
    }

    normalizeTrajectory(trajectory) {
        const container = this.options.containerElement;
        return trajectory.map(p => ({
            x: p.x / container.clientWidth,
            y: p.y / container.clientHeight,
            t: p.timestamp,
            v: p.velocity
        }));
    }

    extractSaccadeProfile() {
        // Extract velocity profile - unique to each person's oculomotor system
        const velocities = this.currentTrajectory.map(p => p.velocity);

        // Downsample to fixed size for comparison
        const profileSize = 20;
        const profile = [];
        const step = Math.max(1, Math.floor(velocities.length / profileSize));

        for (let i = 0; i < profileSize && i * step < velocities.length; i++) {
            const chunk = velocities.slice(i * step, (i + 1) * step);
            profile.push(chunk.reduce((a, b) => a + b, 0) / chunk.length);
        }

        // Normalize profile
        const maxV = Math.max(...profile, 1);
        return profile.map(v => v / maxV);
    }

    complete() {
        this.isRunning = false;

        // Calculate overall signature
        const signature = this.generateSignature();

        if (this.options.onComplete) {
            this.options.onComplete({
                success: true,
                signature: signature,
                rawData: this.challengeData
            });
        }
    }

    generateSignature() {
        // Create a unique signature from the challenge data
        return {
            // Target sequence (normalized positions)
            targetSequence: this.challengeData.targetSequence,

            // Reaction times (unique to person's cognitive processing)
            reactionTimes: {
                values: this.challengeData.reactionTimes,
                mean: this.mean(this.challengeData.reactionTimes),
                std: this.std(this.challengeData.reactionTimes)
            },

            // Fixation accuracies (motor control)
            fixationAccuracies: {
                values: this.challengeData.fixationAccuracies,
                mean: this.mean(this.challengeData.fixationAccuracies)
            },

            // Saccade velocity profiles (oculomotor plant characteristics - UNIQUE)
            saccadeProfiles: this.challengeData.saccadeProfiles,

            // Average saccade profile (for quick comparison)
            avgSaccadeProfile: this.averageProfiles(this.challengeData.saccadeProfiles),

            // Timestamp
            timestamp: Date.now()
        };
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

    averageProfiles(profiles) {
        if (!profiles || profiles.length === 0) return [];

        const profileLength = profiles[0].length;
        const avg = new Array(profileLength).fill(0);

        profiles.forEach(profile => {
            profile.forEach((v, i) => {
                avg[i] += v / profiles.length;
            });
        });

        return avg;
    }

    stop() {
        this.isRunning = false;
    }
}

/**
 * Compare two challenge signatures for authentication
 * Returns similarity score 0-1
 */
function compareGazeSignatures(enrolled, current) {
    if (!enrolled || !current) return 0;

    let totalScore = 0;
    let weights = 0;

    // 1. Compare reaction times (weight: 2)
    if (enrolled.reactionTimes && current.reactionTimes) {
        const rtSimilarity = compareDistributions(
            enrolled.reactionTimes.values,
            current.reactionTimes.values
        );
        totalScore += rtSimilarity * 2;
        weights += 2;
    }

    // 2. Compare fixation accuracies (weight: 1)
    if (enrolled.fixationAccuracies && current.fixationAccuracies) {
        const accSimilarity = compareDistributions(
            enrolled.fixationAccuracies.values,
            current.fixationAccuracies.values
        );
        totalScore += accSimilarity * 1;
        weights += 1;
    }

    // 3. Compare saccade profiles using DTW (weight: 3) - MOST UNIQUE
    if (enrolled.avgSaccadeProfile && current.avgSaccadeProfile) {
        const profileSimilarity = compareSaccadeProfiles(
            enrolled.avgSaccadeProfile,
            current.avgSaccadeProfile
        );
        totalScore += profileSimilarity * 3;
        weights += 3;
    }

    return weights > 0 ? totalScore / weights : 0;
}

function compareDistributions(arr1, arr2) {
    if (!arr1 || !arr2 || arr1.length === 0 || arr2.length === 0) return 0.5;

    const mean1 = arr1.reduce((a, b) => a + b, 0) / arr1.length;
    const mean2 = arr2.reduce((a, b) => a + b, 0) / arr2.length;

    const std1 = Math.sqrt(arr1.reduce((acc, val) => acc + Math.pow(val - mean1, 2), 0) / arr1.length);
    const std2 = Math.sqrt(arr2.reduce((acc, val) => acc + Math.pow(val - mean2, 2), 0) / arr2.length);

    // Compare means (allowing 2 std devs difference)
    const combinedStd = (std1 + std2) / 2 || 1;
    const meanDiff = Math.abs(mean1 - mean2) / combinedStd;
    const meanSimilarity = Math.max(0, 1 - meanDiff / 2);

    // Compare distributions (std should be similar)
    const stdRatio = std1 > 0 && std2 > 0 ? Math.min(std1, std2) / Math.max(std1, std2) : 0.5;

    return meanSimilarity * 0.7 + stdRatio * 0.3;
}

function compareSaccadeProfiles(profile1, profile2) {
    // Use simplified Dynamic Time Warping for sequence comparison
    if (!profile1 || !profile2 || profile1.length === 0 || profile2.length === 0) return 0.5;

    const n = profile1.length;
    const m = profile2.length;

    // Simple correlation-based comparison (faster than full DTW)
    let sumXY = 0, sumX = 0, sumY = 0, sumX2 = 0, sumY2 = 0;
    const len = Math.min(n, m);

    for (let i = 0; i < len; i++) {
        const x = profile1[i];
        const y = profile2[i];
        sumXY += x * y;
        sumX += x;
        sumY += y;
        sumX2 += x * x;
        sumY2 += y * y;
    }

    const numerator = len * sumXY - sumX * sumY;
    const denominator = Math.sqrt((len * sumX2 - sumX * sumX) * (len * sumY2 - sumY * sumY));

    if (denominator === 0) return 0.5;

    const correlation = numerator / denominator;

    // Convert correlation (-1 to 1) to similarity (0 to 1)
    return (correlation + 1) / 2;
}

// Export
window.GazeChallenge = GazeChallenge;
window.compareGazeSignatures = compareGazeSignatures;
