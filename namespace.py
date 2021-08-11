class Namespace:
    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        for kw, arg in kwargs.items():
            if type(arg)==dict:
                setattr(self, kw, Namespace(**arg))
            else:
                setattr(self, kw, arg)

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, index):
        return list(self.__dict__.values())[index]

    def get_from_list(self, arg_list):
        ret_dict = {}
        for arg in arg_list:
            ret_dict[arg] = getattr(self, arg)
        return  ret_dict

    def get(self, arg=None):
        if arg is None:
            return self.get_from_list(self.__dict__.keys())
        return getattr(self, arg)