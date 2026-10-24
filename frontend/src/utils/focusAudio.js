/**
 * Web Audio API Ambient Sound Synthesizer for AI StudySense.
 * 
 * Provides local, offline, privacy-preserving focus audio generators:
 * - White Noise: Flat frequency random noise.
 * - Brown Noise: Deep low-frequency emphasis noise.
 * - Rain Ambiance: Multi-filtered rain texture.
 * - Nature Ambiance: Soft wind & organic resonance.
 * - Lo-Fi Focus Drone: Warm dual-tone harmonic drone with subtle binaural soothing.
 * 
 * Does not require external credentials or third-party streaming hijack.
 */

class FocusAudioEngine {
  constructor() {
    this.ctx = null;
    this.currentSource = null;
    this.gainNode = null;
    this.filterNode = null;
    this.currentType = null;
    this.isPlayingState = false;
  }

  _initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  getProfiles() {
    return [
      { id: "brown", name: "Deep Brown Noise", description: "Warm, low-frequency rumble ideal for deep concentration", icon: "Waves" },
      { id: "white", name: "Pure White Noise", description: "Consistent wide-spectrum noise to mask background distractions", icon: "Radio" },
      { id: "rain", name: "Gentle Rain", description: "Filtered soothing rainfall texture for calm studying", icon: "CloudRain" },
      { id: "nature", name: "Forest Breeze", description: "Soft organic wind and ambient frequency drift", icon: "Wind" },
      { id: "lofi", name: "Lo-Fi Harmonic Drone", description: "Calming 432Hz dual-oscillator alpha focus tone", icon: "Music" },
    ];
  }

  start(type = "brown", volume = 0.5) {
    this.stop();
    this._initContext();

    this.gainNode = this.ctx.createGain();
    this.gainNode.gain.setValueAtTime(volume, this.ctx.currentTime);
    this.gainNode.connect(this.ctx.destination);

    this.currentType = type;

    if (type === "white") {
      this._startWhiteNoise();
    } else if (type === "brown") {
      this._startBrownNoise();
    } else if (type === "rain") {
      this._startRainNoise();
    } else if (type === "nature") {
      this._startNatureNoise();
    } else if (type === "lofi") {
      this._startLoFiDrone();
    } else {
      this._startBrownNoise();
    }

    this.isPlayingState = true;
  }

  stop() {
    if (this.currentSource) {
      try {
        if (Array.isArray(this.currentSource)) {
          this.currentSource.forEach((s) => s.stop());
        } else {
          this.currentSource.stop();
        }
      } catch (err) {
        // Source might already have stopped
      }
      this.currentSource = null;
    }
    this.isPlayingState = false;
    this.currentType = null;
  }

  setVolume(vol) {
    if (this.gainNode && this.ctx) {
      const safeVol = Math.max(0, Math.min(1, vol));
      this.gainNode.gain.setTargetAtTime(safeVol, this.ctx.currentTime, 0.05);
    }
  }

  isPlaying() {
    return this.isPlayingState;
  }

  getCurrentType() {
    return this.currentType;
  }

  _startWhiteNoise() {
    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      output[i] = Math.random() * 2 - 1;
    }

    const whiteNoise = this.ctx.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;
    whiteNoise.connect(this.gainNode);
    whiteNoise.start();
    this.currentSource = whiteNoise;
  }

  _startBrownNoise() {
    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let lastOut = 0.0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      output[i] = (lastOut + 0.02 * white) / 1.02;
      lastOut = output[i];
      output[i] *= 3.5; // Gain compensation
    }

    const brownNoise = this.ctx.createBufferSource();
    brownNoise.buffer = noiseBuffer;
    brownNoise.loop = true;

    // Filter high-frequencies for velvety brown texture
    const filter = this.ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(400, this.ctx.currentTime);

    brownNoise.connect(filter);
    filter.connect(this.gainNode);
    brownNoise.start();
    this.currentSource = brownNoise;
  }

  _startRainNoise() {
    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99765 * b0 + white * 0.0990460;
      b1 = 0.96300 * b1 + white * 0.2965164;
      b2 = 0.57000 * b2 + white * 1.0526913;
      output[i] = (b0 + b1 + b2 + white * 0.1848) * 0.08;
    }

    const rainSource = this.ctx.createBufferSource();
    rainSource.buffer = noiseBuffer;
    rainSource.loop = true;

    const filter = this.ctx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.setValueAtTime(1000, this.ctx.currentTime);
    filter.Q.setValueAtTime(0.7, this.ctx.currentTime);

    rainSource.connect(filter);
    filter.connect(this.gainNode);
    rainSource.start();
    this.currentSource = rainSource;
  }

  _startNatureNoise() {
    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let last = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      last = (last + 0.04 * white) / 1.04;
      output[i] = last * 2.8;
    }

    const source = this.ctx.createBufferSource();
    source.buffer = noiseBuffer;
    source.loop = true;

    const filter = this.ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(650, this.ctx.currentTime);

    source.connect(filter);
    filter.connect(this.gainNode);
    source.start();
    this.currentSource = source;
  }

  _startLoFiDrone() {
    // 216Hz fundamental + 218Hz binaural harmonic (2Hz delta for gentle focus)
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    osc1.type = "sine";
    osc2.type = "triangle";

    osc1.frequency.setValueAtTime(216, this.ctx.currentTime);
    osc2.frequency.setValueAtTime(218, this.ctx.currentTime);

    const filter = this.ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(350, this.ctx.currentTime);

    osc1.connect(filter);
    osc2.connect(filter);
    filter.connect(this.gainNode);

    osc1.start();
    osc2.start();

    this.currentSource = [osc1, osc2];
  }
}

export const focusAudio = new FocusAudioEngine();
