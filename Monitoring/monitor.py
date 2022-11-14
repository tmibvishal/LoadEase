# TODO: add protect each function using @Lock decorator ?
import os
from typing import List, Tuple, Dict, Any
import config
from threading import Thread
import time


class Monitor:
    def __init__(self, vm_ids=None) -> None:
        # Histogram[i] = percentage number of times usage was in [i, i + 5)
        if vm_ids is None:
            vm_ids = []
        self.vm_ids = vm_ids
        self.host_histogram: Dict[int, float] = {i: 0 for i in range(0, 100, 5)}
        self.host_timeseries = []

        self.vm_histograms = {vm_id: {i: 0 for i in range(0, 100, 5)} for vm_id
                              in vm_ids}
        self.vm_timeseries = {vm_id: [] for vm_id in vm_ids}

        self.total_intervals = 0

    # Inheriting classes implement
    # return (host_usage %, and Dict[vmid : vm usage %])
    # Flaot = Percentage, Ex: 95.2 % -> 95.2 (not 0.952)
    def collect_stats(self) -> Tuple[float, Dict[str, float]]:
        pass

    # Inheriting classes implement
    # Implement in base class, add a new vm for monitoring
    def register_vm(self, vm_id) -> None:
        pass

    def update_vm_ids(self, vm_ids: List[str]):
        self.vm_ids = vm_ids
        new_histograms = {vm_id: {i: 0 for i in range(0, 100, 5)} for vm_id in
                          vm_ids}
        new_timeseries = {vm_id: [] for vm_id in vm_ids}
        for vm_id in vm_ids:
            if vm_id in self.vm_histograms:
                assert (vm_id in self.vm_timeseries)
                new_histograms[vm_id] = self.vm_histograms[vm_id]
                new_timeseries[vm_id] = self.vm_timeseries[vm_id]

        self.vm_histograms = new_histograms
        self.vm_timeseries = new_timeseries

    def update(self, host_stat: float, vm_stats: Dict[str, float]) -> None:
        self.total_intervals += 1
        for vm_id, usage in vm_stats.items():
            self.update_histogram(vm_id, usage)
            self.update_timeseries(vm_id, usage)

        self.update_histogram(None, host_stat, host=True)
        self.update_timeseries(None, host_stat, host=True)

    def update_histogram(self, vm_id, resource_usage,
                         host: bool = False) -> None:
        hist = self.host_histogram
        if not host:
            hist = self.vm_histograms[vm_id]

        for interval in range(0, 100, 5):
            if resource_usage >= interval and resource_usage < interval + 5:
                hist[interval] = (hist[interval] * (
                        self.total_intervals - 1) + 1) / self.total_intervals
            else:
                hist[interval] = (hist[interval] * (
                        self.total_intervals - 1)) / self.total_intervals

    def update_timeseries(self, vm_id, resource_usage,
                          host: bool = False) -> None:
        timeseries: List = self.host_timeseries
        if not host:
            timeseries = self.vm_timeseries[vm_id]
        # Fixed / 100
        timeseries.append(resource_usage / 100)
        if len(timeseries) > config.TIME_SERIES_LEN:
            timeseries.pop(0)

    def get_host_stats(self) -> Tuple[List[float], Dict[int, float]]:
        # return Monitor.get_random_timeseries(max=0.4), Monitor.get_random_histogram(max=0.4)
        return self.host_timeseries, self.host_histogram

    def get_vm_stats(self, vm_id: str) -> Tuple[List[float], Dict[int, float]]:
        return self.vm_timeseries[vm_id], self.vm_histograms[vm_id]

    def get_all_vm_stats(self, vm_ids: List[str]):
        # n = len(vm_ids)
        # max = 1 / n
        # return {vm_id: (Monitor.get_random_timeseries(max), Monitor.get_random_histogram(max)) for vm_id in vm_ids}
        return {vm_id: self.get_vm_stats(vm_id) for vm_id in vm_ids}

    @staticmethod
    def get_random_timeseries(max=0.2):
        import random
        return [max * random.random() for i in range(50)]

    @staticmethod
    def get_random_histogram(max=0.2):
        import random
        return {i: max * random.random() for i in range(0, 100, 5)}
