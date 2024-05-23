
def readConfig():
    config = dict()
    # Config파일 읽기
    with open('RDTP.conf', 'r') as f:
        configs = f.readlines()
        for item in configs:
            # 이름과 값 저장하기
            name = str(item.split(" = ")[0])
            value = str(item.split(" = ")[1]).replace("\n", "").replace('"', '')
            config[name] = value
    return config