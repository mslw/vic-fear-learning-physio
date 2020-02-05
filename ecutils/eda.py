import copy


class Trial:
    def __init__(self, events, n_samples, n_bl_samples, fs, signal, smna=None):
        """ Build a representation of a trial.

        events -- list of eventhandler.Event objects
        n_samples -- number of samples to take, starting from 1st event
        n_bl_samples -- number of baseline samples to store
        fs -- sampling frequency
        signal -- preprocessed signal, in alignment with the events
        smna -- sudomotor nerve activity p from cvxEDA (optional)
        """

        start_sample = events[0].sample
        end_sample = start_sample + n_samples
        self.signal = signal[start_sample: end_sample]
        if smna is not None:
            self.smna = smna[start_sample:end_sample]
        else:
            self.smna = None
        self.events = copy.deepcopy(events)
        # deepcopy - event objects should not change in their original context
        # todo: warn if events are beyond <start_sample, end_sample>

        # align events with start of the trial
        for event in self.events:
            event.sample -= start_sample

        # simplify access to types of events present
        self.event_values = [e.value for e in self.events]

        # keep sampling frequency for seconds - samples conversion
        self.fs = fs

        # baseline may or may not be needed depending on scoring method
        # we keep it in reverse order
        self.baseline = signal[start_sample: start_sample - n_bl_samples: -1]

    def plot(self, ax, ax2=None):
        ax.plot(self.signal, color='C1')
        ax.axis('off')

        if ax2 is not None and self.smna is not None:
            ax2.plot(self.smna, color='C2', alpha=0.5)
            ax2.axis('off')

        for e in self.events:
            if e.value in [4, 5, 6]:
                # startle probe
                ax.axvline(e.sample, color='green', linestyle=':')
            elif e.value == 7:
                ax.axvline(e.sample, color='black', linestyle=':')
            elif e.value == 8:
                # shock (obs US)
                ax.axvline(e.sample, color='red', linestyle=':')

    def score_eir(self, onset, duration, baseline_length):

        # get baseline
        if onset == 0:
            # take baseline from self.baseline
            bl_end_smp = int(baseline_length * self.fs)
            if bl_end_smp > len(self.baseline):
                raise ValueError('Baseline too long')
            baseline = self.baseline[:bl_end_smp]
        else:
            # take baseline from self.signal
            bl_start_smp = int((onset - baseline_length) * self.fs)
            bl_end_smp = int(onset * self.fs)
            if bl_start_smp < 0:
                # this could be mitigated, but is unlikely to be useful
                raise ValueError('For start > 0, baseline is too long')
            baseline = self.signal[bl_start_smp: bl_end_smp]

        # get response
        r_start_smp = int(onset * self.fs)
        r_end_smp = int((onset + duration) * self.fs)
        response = self.signal[r_start_smp: r_end_smp]

        # calculate amplitude & peak time
        amplitude = response.max() - baseline.mean()
        peak_time = onset + response.argmax() / self.fs

        # TODO: change return type
        if amplitude > 0.02:
            return amplitude, peak_time
        else:
            return None, None

    def score_smna(self, onset, duration):

        if self.smna is None:
            return None

        r_start_smp = int(onset * self.fs)
        r_end_smp = int((onset + duration) * self.fs)
        response = self.smna[r_start_smp: r_end_smp]

        amplitude = response.sum()
        peak_time = None

        # TODO: change return type
        return(amplitude, peak_time)

    def score_peak_to_peak(self, onset, duration, footpoint_limit):
        raise NotImplementedError
