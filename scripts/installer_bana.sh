#!/bin/bash
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -o errexit
echo ""
echo "Bắt đầu chương trình cài đặt tự động cho Bananapi"
echo ""
scripts_dir="$(dirname "${BASH_SOURCE[0]}")"
GIT_DIR="$(realpath $(dirname ${BASH_SOURCE[0]})/..)"

# make sure we're running as the owner of the checkout directory
RUN_AS="$(ls -ld "$scripts_dir" | awk 'NR==1 {print $3}')"
if [ "$USER" != "$RUN_AS" ]
then
    echo "Tập lệnh này phải chạy dưới dạng $ RUN_AS, đang cố gắng thay đổi người dùng..."
    exec sudo -u $RUN_AS $0
fi
clear
echo ""
read -r -p "Nhập tên file .json, Vui lòng chép file này thư mục /home/pi: " credname

sudo apt-get update -y
sed 's/#.*//' ${GIT_DIR}/scripts/system.txt | xargs sudo apt-get install -y


#Check OS Version
echo ""
echo "Kiểm tra khả năng tương thích của hệ điều hành"
echo ""
if [[ $(cat /etc/os-release|grep "raspbian") ]]; then
  if [[ $(cat /etc/os-release|grep "stretch") ]]; then
    osversion="Raspbian Stretch"
    echo ""
    echo "Bạn đang chạy trình cài đặt Raspbian Stretch ="
    echo ""
  elif [[ $(cat /etc/os-release|grep "buster") ]]; then
    osversion="Raspbian Buster"
    echo ""
    echo "Bạn đang chạy trình cài đặt Raspbian Buster"
    echo ""
  else
    osversion="Other Raspbian"
    echo ""
    echo "Bạn nên sử dụng phiên bản Stretch hoặc Buster"
    echo "Thoát khỏi trình cài đặt"
    echo ""
    exit 1
  fi
elif [[ $(cat /etc/os-release|grep "armbian") ]]; then
  if [[ $(cat /etc/os-release|grep "stretch") ]]; then
    osversion="Armbian Stretch"
    echo ""
    echo "Bạn đang chạy trình cài đặt trên Armbian Stretch"
    echo ""
  else
    osversion="Other Armbian"
    echo ""
    echo "Bạn nên sử dụng phiên bản Armbian Stretch"
    echo "Thoát khỏi trình cài đặt="
    echo ""
    exit 1
  fi
elif [[ $(cat /etc/os-release|grep "osmc") ]]; then
  osmcversion=$(grep VERSION_ID /etc/os-release)
  osmcversion=${osmcversion//VERSION_ID=/""}
  osmcversion=${osmcversion//'"'/""}
  osmcversion=${osmcversion//./-}
  osmcversiondate=$(date -d $osmcversion +%s)
  export LC_ALL=C.UTF-8
  export LANG=C.UTF-8
  if (($osmcversiondate > 1512086400)); then
    osversion="OSMC Stretch"
    echo ""
    echo "Compatible OSMC version"
    echo ""
  else
    osversion="Other OSMC"
    echo ""
    echo "You are advised to use atleast the Stretch version of the OS"
    echo "Exiting the installer="
    echo ""
    exit 1
  fi
elif [[ $(cat /etc/os-release|grep "ubuntu") ]]; then
  if [[ $(cat /etc/os-release|grep "bionic") ]]; then
    osversion="Ubuntu Bionic"
    echo ""
    echo "You are running the installer on Bionic"
    echo ""
  else
    osversion="Other Ubuntu"
    echo ""
    echo "You are advised to use the Bionic version of the OS"
    echo "Exiting the installer="
    echo ""
    exit 1
  fi
fi

#Check CPU architecture
if [[ $(uname -m|grep "armv7") ]] || [[ $(uname -m|grep "x86_64") ]] || [[ $(uname -m|grep "armv8") ]]; then
	devmodel="armv7"
  echo ""
  echo "Thiết bị của bạn hỗ trợ Hotword Ok-Google . Bạn cũng có thể kích hoạt trợ lý bằng cách sử dụng từ khóa tùy chỉnh"
  echo ""
else
	devmodel="armv6"
  echo ""
  echo "Thiết bị của bạn không hỗ trợ Hotword Ok-Google . Bạn cần kích hoạt trợ lý bằng cách sử dụng khóa tùy chỉnh"
  echo ""
fi

#Check Board Model
if [[ $(cat /proc/cpuinfo|grep "BCM") ]]; then
	board="Raspberry"
  echo ""
  echo "GPIO pins can be used with the assistant"
  echo ""
else
	board="Others"
  echo ""
  echo "GPIO pins cannot be used by default with the assistant. You need to figure it out by yourselves"
  echo ""
fi

cd /home/${USER}/ViPi/
#sudo python3 -m venv env
#env/bin/sudo python -m pip install --upgrade pip setuptools wheel
#sudo env/bin/python3 -m pip install --upgrade pip setuptools wheel
#source env/bin/activate
sudo python3 -m pip install --upgrade pip setuptools wheel
sudo python3 -m pip install -r scripts/pip.txt

if [[ $board = "Raspberry" ]] && [[ $osversion != "OSMC Stretch" ]];then
	sudo python3 -m pip install RPi.GPIO>=0.6.3
  sudo sed -i -e "s/^autospawn=no/#\0/" /etc/pulse/client.conf.d/00-disable-autospawn.conf
  if [ -f /lib/udev/rules.d/91-pulseaudio-rpi.rules ] ; then
      sudo rm /lib/udev/rules.d/91-pulseaudio-rpi.rules
  fi
fi

if [[ $devmodel = "armv7" ]];then
	sudo python3 -m pip install google-assistant-library==1.1.0
else
    sudo python3 -m pip install --upgrade --no-binary :all: grpcio==1.36.1
    #pip install grpcio==1.36.1  
fi

sudo python3 -m pip install google-assistant-grpc==0.3.0
sudo python3 -m pip install google-assistant-sdk==0.6.0
sudo python3 -m pip install google-assistant-sdk[samples]==0.6.0
google-oauthlib-tool --scope https://www.googleapis.com/auth/assistant-sdk-prototype \
          --scope https://www.googleapis.com/auth/gcm \
          --save --headless --client-secrets $credname

echo ""
echo ""
echo "Hoàn thành cài đặt, vui lòng reboot........"
