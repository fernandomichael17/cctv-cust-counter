from collections import defaultdict

class CrossingCounter:
    """Track IDs are local to a camera. Count a transition between stable line sides."""
    def __init__(self, p1, p2, inside_side=1, margin=0.025):
        self.p1, self.p2 = p1, p2
        self.inside_side = inside_side
        self.margin = margin
        self.sides = {}
        self.last_seen = {}
        self.tick = 0

    def side(self, x, y):
        ax, ay = self.p1
        bx, by = self.p2
        length = ((bx-ax)**2 + (by-ay)**2)**0.5
        if length == 0:
            raise ValueError('Line endpoints must differ')
        signed = ((bx-ax)*(y-ay) - (by-ay)*(x-ax))/length
        if signed > self.margin: return 1
        if signed < -self.margin: return -1
        return 0

    def update(self, tracks):
        """tracks: iterable of (track_id, normalized_x, normalized_y)."""
        self.tick += 1
        events = []
        for tid, x, y in tracks:
            s = self.side(x,y)
            self.last_seen[tid] = self.tick
            if s == 0:
                continue
            old = self.sides.get(tid)
            if old is not None and old != s:
                events.append('IN' if s == self.inside_side else 'OUT')
            self.sides[tid] = s
        if self.tick % 300 == 0:
            stale = [tid for tid, t in self.last_seen.items() if self.tick-t > 150]
            for tid in stale:
                self.last_seen.pop(tid, None)
                self.sides.pop(tid, None)
        return events
