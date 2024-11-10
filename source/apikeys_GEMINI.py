class APIKeyManager:
    def __init__(self, keys):
        self.keys = {key: 0 for key in keys}  # Khởi tạo key với số lần sử dụng bằng 0
        self.index = 0
        self.key_list = list(self.keys.keys())

    def get_next_key(self):
        # Kiểm tra nếu tất cả các key đều có số lần sử dụng bằng nhau
        if len(set(self.keys.values())) == 1:
            self.index = 0  # Đặt lại chỉ số

        key = self.key_list[self.index]
        self.keys[key] += 1  # Tăng số lần sử dụng của key
        self.index = (self.index + 1) % len(self.key_list)
        return key

    def get_key_usage(self):
        return self.keys