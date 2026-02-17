class DbMetric:

    def __init__(self):
        self.opn = ""
        self.obj = ""
        self.component = ""
        self.errorct = 0
        self.count = 0
        self.time = 0
        self.minrt = None
        self.maxrt = None

    def accumulate(self, dbtracker):
        info = dbtracker.get_info()
        if "opn" not in info or "obj" not in info:
            return

        self.opn = info["opn"]
        self.obj = info["obj"]
        self.component = dbtracker.get_component()
        if dbtracker.is_error():
            self.errorct += 1
            return

        self.time += dbtracker.get_rt()
        self.count += 1
        if self.minrt is None or dbtracker.get_rt() < self.minrt:
            self.minrt = dbtracker.get_rt()

        if self.maxrt is None or dbtracker.get_rt() > self.minrt:
            self.maxrt = dbtracker.get_rt()

    def get_formatted_dbmetric(self):
        return [self.time, self.minrt, self.maxrt, self.count, self.errorct]

    def get_opn(self):
        return self.opn

    def get_obj(self):
        return self.obj
