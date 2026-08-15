"""Encodes prosthetic touch/force sensor data into peripheral-nerve
stimulation pulse parameters, with hard charge-density safety ceilings.

Charge-balanced, current-controlled biphasic pulses are used (standard
practice for chronic peripheral nerve stimulation to avoid net DC injection
and electrode/tissue damage). All limits below are conservative reference
defaults, not a clinical prescription — actual limits must be set per
electrode geometry and clinician-approved protocol.
"""
from __future__ import annotations

from dataclasses import dataclass


class StimulationSafetyError(ValueError):
    """Raised when a requested stimulation parameter exceeds a hard safety ceiling."""


@dataclass(frozen=True)
class StimulationPulse:
    amplitude_ma: float
    pulse_width_us: float
    frequency_hz: float
    charge_per_phase_nc: float
    channel: int


@dataclass
class SensoryEncoder:
    max_amplitude_ma: float = 5.0
    max_pulse_width_us: float = 200.0
    max_frequency_hz: float = 300.0
    max_charge_per_phase_nc: float = 1000.0  # nC/phase safety ceiling (reference value)

    def encode_force(self, channel: int, normalized_force: float) -> StimulationPulse:
        """Map normalized contact force (0..1) to a biphasic stimulation pulse.

        Uses an amplitude-modulation scheme (fixed pulse width/frequency,
        amplitude scaled with force) — generally preferred for perceptual
        linearity and predictable charge injection versus modulating width.
        """
        normalized_force = max(0.0, min(1.0, normalized_force))

        amplitude_ma = normalized_force * self.max_amplitude_ma
        pulse_width_us = 100.0  # fixed, within max_pulse_width_us
        frequency_hz = 50.0 + normalized_force * 50.0  # 50-100 Hz range

        charge_per_phase_nc = amplitude_ma * pulse_width_us  # nC = mA * us (1 mA*1us = 1 nC)

        pulse = StimulationPulse(
            amplitude_ma=amplitude_ma,
            pulse_width_us=pulse_width_us,
            frequency_hz=frequency_hz,
            charge_per_phase_nc=charge_per_phase_nc,
            channel=channel,
        )
        self._validate(pulse)
        return pulse

    def _validate(self, pulse: StimulationPulse) -> None:
        if pulse.amplitude_ma > self.max_amplitude_ma:
            raise StimulationSafetyError(f"Amplitude {pulse.amplitude_ma}mA exceeds ceiling {self.max_amplitude_ma}mA")
        if pulse.pulse_width_us > self.max_pulse_width_us:
            raise StimulationSafetyError(f"Pulse width {pulse.pulse_width_us}us exceeds ceiling {self.max_pulse_width_us}us")
        if pulse.frequency_hz > self.max_frequency_hz:
            raise StimulationSafetyError(f"Frequency {pulse.frequency_hz}Hz exceeds ceiling {self.max_frequency_hz}Hz")
        if pulse.charge_per_phase_nc > self.max_charge_per_phase_nc:
            raise StimulationSafetyError(
                f"Charge/phase {pulse.charge_per_phase_nc}nC exceeds ceiling {self.max_charge_per_phase_nc}nC"
            )
