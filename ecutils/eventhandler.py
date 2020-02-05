import numpy as np
import copy


class Event:
    def __init__(self, sample, value):
        self.sample = sample
        self.value = value

    def __str__(self):
        return 'Event: (' + str(self.sample) + ', ' + str(self.value) + ')'


class EventCollection:
    def __init__(self):
        self.events = []

    @classmethod
    def from_acq(cls, data_obj, first_digital_index=2, width=10):
        """Create a collection of events from AcqKnowledge data

        Arguments:
        # data_obj -- bioread object representing Acq data
        # first_digital_index -- index of first digital channels
        # width -- number of samples to check for co-ocurring events
        """

        ec = cls()

        n_samples = data_obj.channels[first_digital_index].point_count
        binary_onsets = np.zeros([8, n_samples - 1], dtype=np.int)

        # detect rising edges and store them in an array
        for i in range(8):
            chan = data_obj.channels[first_digital_index + i]
            d = (chan.data > 2.5).astype(np.int)  # binary (0/1)
            edges = (np.diff(d) > 0).astype(np.int)   # rising edges

            binary_onsets[i] = edges

        i = 0
        while i < n_samples - 1:
            # go sample by sample

            if np.sum(binary_onsets[:, i]) > 0:
                # if there was a rising edge on one of the channels
                # check neigborhood on all channels & convert to decimal
                fragment = binary_onsets[:, i:i+width]
                vec = np.max(fragment, axis=1)
                marker_value = cls.to_decimal(vec)
                ec.events.append(Event(i, marker_value))  # <<<< TUTAJ
                i += width
            else:
                i += 1

        return ec

    @classmethod
    def from_txt(cls, file_name):
        """Create a collection of events from text file"""

        ec = cls()

        with open(file_name) as f:
            lines = f.readlines()
            for line in lines:
                onset, value = line.rstrip().split()
                ec.events.append(Event(int(onset), int(value)))
        return ec

    @classmethod
    def from_list(cls, events_list, reset_samples=True):
        """Create a new collection of events from a list of events"""

        ec = cls()

        ec.events = copy.deepcopy(events_list)
        if reset_samples:
            zero = ec.events[0].sample
            for e in ec.events:
                e.sample -= zero

        return ec

    @staticmethod
    def to_decimal(vec):
        places = np.nonzero(vec)[0]
        pwr = np.power(2, places)
        return np.sum(pwr)

    def to_txt(self, file_name):
        with open(file_name, 'wt') as f:
            for e in self.events:
                f.write('{}\t{}\n'.format(e.sample, e.value))

    def downsample(self, factor):
        for event in self.events:
            event.sample = int(round(event.sample / factor))

    def all_events(self):
        return self.events

    def as_marker_list(self):
        return [event.value for event in self.events]

    def samples_for_marker(self, m):
        return [event.sample for event in self.events if event.value == m]

    def remove_at_index(self, x):
        self.events.pop(x)

    def remove_before_index(self, x):
        self.events = self.events[x:]

    def events_between_samples(self, start, stop):
        return [event for event in self.events if start <= event.sample < stop]

    def events_between_events(self, start_marker, stop_marker):
        append = False
        matching_events = []
        for event in self.events:
            if event.value == start_marker:
                append = True
            elif event.value == stop_marker:
                append = False

            if append:
                matching_events.append(event)

        return matching_events
