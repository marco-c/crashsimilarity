class ThresholdClusterizer(object):
    def __init__(self, thresh_hold):
        self.thresh_hold = thresh_hold

    def are_similar(self, score):
        return score > self.thresh_hold
