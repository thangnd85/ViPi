import platform, os, yaml, json, time
ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))
with open('{}/src/config.yaml'.format(ROOT_PATH),'r', encoding='utf8') as conf:
    configuration = yaml.safe_load(conf)
try:      
    with open('{}/.config/google-oauthlib-tool/credentials.json'.format(USER_PATH), 'r') as registers:
        register = json.load(registers)
    register=False
except:
    register=True
if register:
    print('Bạn chưa đăng ký tài khoản với google, thực hiện đăng ký tài khoản')
    from new_oauth import *
    if __name__ == '__main__':
       app.run(host='0.0.0.0',port=5002)
    pass
else:
    if configuration['Start_config']['Startup_file']=='new_main':
        import new_main
        print ('\nimport new_main')
        new_main.Myassistant().main()
    if configuration['Start_config']['Startup_file']=='new_start':
        import new_start
        print ('\nimport new_start')
        new_start.main()
    # else:
        # from actions import say_save
        # say_save('đã xảy ra lỗi,vui lòng kiểm tra cài đặt và khởi động lại')
        # time.sleep(5)
        # pass