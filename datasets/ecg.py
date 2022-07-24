from typing import Tuple
from typing import Union

import numpy as np
import torch
import mne

from datasets.base import BaseDataset

class ECG(BaseDataset):
    def __init__(self, path, name='ecg', seg_len = 30, InD = None):
        super(ECG, self).__init__()
        self.path = path
        self.InD = InD
        self.name = name
        self.seg_len = seg_len # length of a segment, e.g. 10s, 30s
        self.freq = 250  # sampling rate = 250 Hz

        file03 = f"{path}/slp03.edf"
        file04 = f"{path}/slp04.edf"
        file14 = f"{path}/slp14.edf"
        file16 = f"{path}/slp16.edf"

        data03 = mne.io.read_raw_edf(file03)
        data04 = mne.io.read_raw_edf(file04)
        data14 = mne.io.read_raw_edf(file14)
        data16 = mne.io.read_raw_edf(file16)

        def normalize01(x):
            # 0-1 normalization
            max_x = np.max(x)
            min_x = np.min(x)
            return (x - min_x) / (max_x - min_x)

        # e.g. shape=(5400000,) => reshape into (720, 7500), and normalize into [0,1]
        ecg03 = normalize01(data03.get_data()[0][:5400000].reshape(-1, 1, 1, self.seg_len * self.freq))
        ecg04 = normalize01(data04.get_data()[0][:5400000].reshape(-1, 1, 1, self.seg_len * self.freq))
        ecg14 = normalize01(data14.get_data()[0][:5400000].reshape(-1, 1, 1, self.seg_len * self.freq))
        ecg16 = normalize01(data16.get_data()[0][:5400000].reshape(-1, 1, 1, self.seg_len * self.freq))

        self.ecg = torch.from_numpy(np.concatenate((ecg03, ecg04, ecg14, ecg16))).float()
        indices = np.arange(self.ecg.shape[0])
        np.random.shuffle(indices)
        self.shuffled_idx = indices

        self.val_idxs = None  # 10%
        self.train_idxs = None # 80%
        self.test_idxs = None  # 10%

    def val(self, InD):
        self.mode = 'val'
        self.val_idxs = self.shuffled_idx[int(0.8 * len(self.shuffled_idx)):int(0.9 * len(self.shuffled_idx))]
        self.length = len(self.val_idxs)

    def train(self, InD):
        self.mode = 'train'
        self.train_idxs = self.shuffled_idx[0:int(0.8 * len(self.shuffled_idx))]
        self.length = len(self.train_idxs)
        # shuffle the training set manually
        np.random.shuffle(self.train_idxs)
        print(f"Training Set prepared, Num:{self.length}")

    def test(self, InD):
        self.mode = 'test'
        print(f"Test set contains ECG")
        self.test_idxs = self.shuffled_idx[int(0.9 * len(self.shuffled_idx)):]
        self.length = len(self.test_idxs)

    def __len__(self):
        # type: () -> int
        """
        Returns the number of examples.
        """
        return self.length

    def __getitem__(self, i):
        # type: (int) -> Tuple[torch.Tensor, Union[torch.Tensor, int]]
        """
        Provides the i-th example.
        """

        # Load the i-th example
        if self.mode == 'test':
            x = self.ecg[self.test_idxs[i]]
            sample = x, x

        elif self.mode == 'val':
            x = self.ecg[self.val_idxs[i]]
            sample = x, x

        elif self.mode == 'train':
            x = self.ecg[self.train_idxs[i]]
            sample = x, x
        else:
            raise ValueError

        return sample

    @property
    def shape(self):
        # type: () -> Tuple[int, int, int]
        """
        Returns the shape of examples.
        """
        return 1, 1, self.seg_len*self.freq

    def __repr__(self):
        return ("OOD detection on ECG (InD = {} )").format(self.InD)