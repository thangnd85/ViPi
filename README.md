### Dự án bot [ViPi] là dự án mod lại từ các dự án sau:
https://github.com/googlesamples/assistant-sdk-python/tree/master/google-assistant-sdk
https://github.com/shivasiddharth/GassistPi
Với sự đóng góp các thành viên mù code và tester đam mê phá nhà, nghèo vì độ loa sẽ update trong contributer sau :D

Đây là dự án miễn phí, phục vụ cá nhân khi rảnh rỗi, không phải dev chuyên nghiệp. Anh em muốn tham gia vào đội coder thì cứ inbox m.me/thangnd85 hoặc t.me/thangnd85
### 1.Tải OS tại đây:
http://www.cs.tohoku-gakuin.ac.jp/pub/Linux/RaspBerryPi/

### 2.Update OS & cài đặt git:
```sh
sudo apt-get update && sudo apt-get install git -y
```
### 3. Cài đặt Mic & Loa nếu sử dụng Mic HAT:
OS trước tháng 8.2020
```sh
cd /home/${USER}/
git clone https://github.com/respeaker/seeed-voicecard.git
cd seeed-voicecard
sudo ./install.sh --compat-kernel
sudo reboot
```
OS sau tháng 8.2020
```sh
cd /home/${USER}/
git clone https://github.com/HinTak/seeed-voicecard
cd seeed-voicecard
sudo ./install.sh
sudo reboot now
```
Sau khi khởi động lại, đăng nhập lại vào console
Kiểm tra xem có âm thanh ở loa hay không:
```sh
speaker-test
```
Lệnh Thống kê ID của Mic USB và Loa
```sh
arecord -l
aplay -l
```
==> chuyển sang bước 5:
### 4. Khai báo khi sử dụng Mic Usb:
Lệnh Thống kê ID của Mic USB và Loa
```sh
arecord -l
aplay -l
```
Chạy lệnh sau
```sh
sudo nano /home/pi/.asoundrc
```
Cửa sổ nano hiện lên, paste dòng sau, thay thế ID mic, loa phù hợp

```sh
pcm.dsnooper {
    type dsnoop
    ipc_key 816357492
    ipc_key_add_uid 0
    ipc_perm 0666
    slave {
        pcm "hw:1,0"
        channels 1
    }
}

pcm.!default {
        type asym
        playback.pcm {
                type plug
                slave.pcm "hw:0,0"
        }
        capture.pcm {
                type plug
                slave.pcm "dsnooper"
        }
}

```
Coppy cấu hình âm thanh vào etc:
```sh
sudo cp /home/pi/.asoundrc /etc/asound.conf
```
Đưa Account đang dùng (Ví dụ pi) vào group root:
```sh
sudo usermod -aG root pi
```
###
### Cài portaudio:
Tải về từ git:
```sh
git clone -b alsapatch https://github.com/gglockner/portaudio
cd portaudio
./configure && make
sudo make install
sudo ldconfig
```


Khởi động lại

```sh
sudo reboot
```
Nếu vẫn còn xuất hiện lỗi cài bổ sung các thư viện bổ sung của pulseaudio
```sh
sudo apt-get install pulseaudio -y && sudo apt-get remove pulseaudio -y
```


### 5. Chọn loại led trong file config.yaml
```sh
  #  Set type mic to:
  # 1. 'GEN'   ---> USB-MIC-JACK
  # 2. 'GEN'   ---> USB-MIC-HDMI
  # 3. 'AIY'   ---> AIY-HAT
  # 4. 'R2M'   ---> Respeaker-2-Mic
  # 5. 'R4M'   ---> Respeaker-4-Mic
  # 6. 'RUM'   ---> Respeaker-Usb-Mic
  # 7. 'NEO'   ---> NeoPixel
  # 8. 'GOO'   ---> Google
  # 8. 'ALE'   ---> Alexa
```
### 6.Tải git & cài đặt:

Chạy lệnh sau để cài đặt trên môi trường ảo hóa:
```sh
 sudo chmod +x ./ViPi/scripts/installer.sh && sudo  ./ViPi/scripts/installer.sh
```

```
### 7.Chạy lần đầu:
Chạy lần đầu với raspi:
```sh
env/bin/python -u ./ViPi/src/start.py --project-id 'XXX' --device-model-id 'XXX'
```

### 8.Chạy thủ công các lần tiếp theo:
Chạy thủ công với raspi:
```sh
env/bin/python -u ./ViPi/src/start.py
```

```
Đăng ký thủ công nếu bỏ qua bước nhập json thay thế $credname thành vị trí file json tương ứng:
```sh
google-oauthlib-tool --scope https://www.googleapis.com/auth/assistant-sdk-prototype \
          --scope https://www.googleapis.com/auth/gcm \
          --save --headless --client-secrets $credname
```
### 9.Thiết lập chạy tự động:
a. Chạy tự động với supervisor:
```sh
sudo nano /etc/supervisor/conf.d/ViPi.conf
```
Cửa sổ nano hiện lên, paste dòng sau
```sh
[program:ViPi]
directory=/home/pi
command=/bin/bash -c 'env/bin/python -u ./ViPi/src/start.py'
numprocs=1
autostart=true
autorestart=true
user=pi
```
Chạy lệnh sau để khởi động chạy tự động:
```sh
sudo supervisorctl update
```
Xong reboot lại Pi:
```sh
sudo reboot
```
b. Chạy tự động với crontab -e:

```sh
sudo cp /home/pi/ViPi/run_vipi.py /home/pi/run_vipi.py
crontab -e
```
chọn 1 và paste line to the end, press ctrl + X, Y. Then reboot Pi

```sh
@reboot python -u /home/pi/run_vipi.py
```
### 10.Tắt chạy tự động trong phiên làm việc:

```sh
sudo supervisorctl stop ViPi
```
### 11.Xóa chạy tự động:
```sh
sudo rm -rf /etc/supervisor/conf.d/ViPi.conf
```
### 12. Tạo STT tại đây:

-  Đăng ký Acc FPT AI tại: https://fpt.ai/

-  Đăng ký Acc Viettel AI tại: https://viettelgroup.ai/en

-  Đăng ký Acc Zalo AI tại: https://zalo.ai/user-profile



### 14. Note!
fix: NotImplementedError: mixer module not available (ImportError: libSDL2_mixer-2.0.so.0: cannot open shared object file: No such file or directory)
```sh
sudo dpkg --configure -a
#sudo apt-get install libsdl-ttf2.0-0
#sudo apt-get install libsdl2-mixer-2.0-0
sudo apt-get install python3-sdl2 -y
sudo apt install libportaudio2;
```
Đưa lệnh vào env với raspi:
```sh
source env/bin/activate
```
Đưa lệnh vào env với bananapi:
```sh
source ViPi/env/bin/activate
```
Cài thêm app:
```sh
pip install pygame
```
Hạ phiên bản VLC:
```sh
source env/bin/activate
pip install python-vlc==3.0.11115
```

### Fix pluseaudio
```sh   
cd /home/${USER}/       
git clone https://github.com/shivasiddharth/PulseAudio-System-Wide       
cd ./PulseAudio-System-Wide/      
sudo cp ./pulseaudio.service /etc/systemd/system/pulseaudio.service    
systemctl --system enable pulseaudio.service       
systemctl --system start pulseaudio.service       
sudo cp ./client.conf /etc/pulse/client.conf        
sudo sed -i '/^pulse-access:/ s/$/root,pi/' /etc/group    
```
#### Một số khẩu lệnh:

```sh
Tăng/giảm âm thanh: tăng thêm/giảm bớt âm lượng 0-100 
Tăng giảm âm thanh: đặt/thay đổi âm lượng lớn nhất/ tối thiểu
Tăng giảm âm thanh: đặt/thay đổi âm lượng 0-100
Tắt nhạc: tắt nhạc
Chuyển bài chỉ áp dụng khi phát tự động: bài tiếp theo/ bài hát trước
Phát một bài hát: Phát bài, phát nhạc+()
Phát nhiều bài bài hát khi dùng start.py: Phát tự động + (), phát danh sách+()
Phát nhiều bài bài hát khi dùng start.py: Phát + ()
phát radio:   radio + (tên đài) ví dụ Radio bà rịa vũng tàu
Lịch âm: Lịch âm hoặc âm lịch + (hôm nay, qua , mai ,mốt)
Thay đổi âm lượng giọng nói: âm lượng tăng/ âm lượng giảm ( tự động +/-5% đối với pi zero, +/-10% đối với pi3 trở lên)
```
https://installvirtual.com/install-python-3-7-on-raspberry-pi/


sudo chmod -R o+rwx /directory  

### Chuyển json vào root 

Password: điền pass.không biết pass thì tạo pass mới.

```sh
sudo passwd root
sudo su
cd ~
cd .config
mkdir google-oauthlib-tool
sudo cp /home/pi/.config/google-oauthlib-tool/credentials.json /root/.config/google-oauthlib-tool/credentials.json
```
## config Nếu dùng led W2812
```sh
sudo usermod -aG spi pi
sudo nano /boot/config.txt
```
#Add thêm 2 dòng sau
```sh
core_freq=250
spidev.bufsiz=32768
```
Reboot lại thiết bị
