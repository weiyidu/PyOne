#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# ====================================================
# Description:PyOne 一键脚本 for Debian 8+ 、CentOS 7、Ubuntu 16+
# ====================================================

#fonts color
Red="\033[31m"
Font="\033[0m"
Blue="\033[36m"
cur_path=`pwd`

check_port() {
        netstat -tlpn | grep "\b$1\b"
}
#root permission
check_root(){
        if [[ $EUID -ne 0 ]]; then
        echo "${Red}Error:请使用root运行该脚本！"${Font} 1>&2
        exit 1
        fi
}

#check system
check_system(){
        if [[ -f /etc/redhat-release ]]; then
        release="centos"
    elif cat /etc/issue | grep -Eqi "debian"; then
        release="debian"
    elif cat /etc/issue | grep -Eqi "ubuntu"; then
        release="ubuntu"
    elif cat /etc/issue | grep -Eqi "centos|red hat|redhat"; then
        release="centos"
    elif cat /proc/version | grep -Eqi "debian"; then
        release="debian"
    elif cat /proc/version | grep -Eqi "ubuntu"; then
        release="ubuntu"
    elif cat /proc/version | grep -Eqi "centos|red hat|redhat"; then
        release="centos"
    fi
}

#check version
check_version(){
    if [[ -s /etc/redhat-release ]]; then
     version=`cat /etc/redhat-release|sed -r 's/.* ([0-9]+)\..*/\1/'`
    else
     version=`grep -oE  "[0-9.]+" /etc/issue | cut -d . -f 1`
    fi
    bit=`uname -m`
    if [[ ${bit} = "x86_64" ]]; then
        bit="64"
    else
        bit="32"
    fi
    if [[ "${release}" = "centos" && ${version} -ge 7 ]];then
        echo -e "${Blue}当前系统为CentOS ${version}${Font} "
    elif [[ "${release}" = "debian" && ${version} -ge 8 ]];then
        echo -e "${Blue}当前系统为Debian ${version}${Font} "
    elif [[ "${release}" = "ubuntu" && ${version} -ge 16 ]];then
        echo -e "${Blue}当前系统为Ubuntu ${version}${Font} "
    else
        echo -e "${Red}脚本不支持当前系统，安装中断!${Font} "
        exit 1
    fi
    for EXE in grep cut xargs systemctl ip awk
    do
        if ! type -p ${EXE}; then
            echo -e "${Red}系统精简厉害，脚本自动退出${Font}"
            exit 1
        fi
    done
}


check_service(){
    read -p "请输入redis端口号[6379]:" redis_port
    if [ -z "${redis_port}" ];then
        redis_port=6379
    fi

    read -p "请输入MongoDB端口号[27017]:" mongo_port

    if [ -z "${mongo_port}" ];then
        mongo_port=27017
    fi


    if check_port ${redis_port}; then
        echo ""
    else
        echo -e "${Red}Error:请先在宝塔安装redis"${Font} 1>&2
        exit 1
    fi

    if check_port ${mongo_port}; then
        echo ""
    else
        echo -e "${Red}Error:请先在宝塔安装MongoDB"${Font} 1>&2
        exit 1
    fi
}

#enter info
enter(){
    stty erase '^H' && read -p "请设置Aria2密钥:" aria2_pass
    sed -i "s/ARIA2_SECRET=\"abbey\"/ARIA2_SECRET=\"${aria2_pass}\"/g" self_config.py

    read -p "请设置PyOne的后台密码:" pyone_pass
    sed -i "s/password=\"PyOne\"/password=\"${pyone_pass}\"/g" self_config.py
}


config_file(){
    cur_dir=`pwd`
    cp self_config.py.sample self_config.py
    sed -i "s|/root/PyOne|$cur_dir|" self_config.py
}



#install depend
install_depend(){
echo -e "${Blue}开始安装依赖${Font}"
    if [[ "${release}" = "centos" ]]; then
        yum -y install make git gcc crontabs lsof unzip python-devel libffi-devel openssl-devel -y
    else
        apt update -y
        apt install -y make git cron build-essential python-dev lsof unzip python-setuptools python-wheel libffi-devel libssl-dev
    fi
}


#install aria2
install_aria2(){
    echo -e "${Blue}开始安装Aria2...${Font}"
    wget -N --no-check-certificate https://www.moerats.com/usr/shell/PyOne/aria2-1.34.0-linux-${bit}.tar.gz
    tar zxvf aria2-1.34.0-linux-${bit}.tar.gz
    rm -rf aria2-1.34.0-linux-${bit}.tar.gz
    cd aria2-1.34.0-linux-${bit}
    make install
     EXEC="$(command -v aria2c)"
        if [[ -n ${EXEC} ]]; then
            echo -e "${Blue}Aria2安装成功！${Font}"
        else
            echo -e "${Red}Aria2安装失败！${Font}"
            exit 1
        fi
    cd ..
    rm -rf aria2-1.34.0-linux-${bit}
    mkdir "/root/.aria2" && mkdir /root/Download
    wget -N --no-check-certificate https://www.moerats.com/usr/shell/Aria2/dht.dat -P '/root/.aria2/'
    wget -N --no-check-certificate https://www.moerats.com/usr/shell/PyOne/aria2.conf -P '/root/.aria2/'
    wget -N --no-check-certificate https://www.moerats.com/usr/shell/PyOne/trackers-list-aria2.sh -P '/root/.aria2/'
    touch /root/.aria2/aria2.session
    chmod +x /root/.aria2/trackers-list-aria2.sh
    chmod 777 /root/.aria2/aria2.session
    sed -i "s/rpc-secret=/rpc-secret=${aria2_pass}/g" /root/.aria2/aria2.conf
    echo -e "${Blue}开始设置trackers-list自动更新！${Font}"
    if [[ "${release}" = "centos" ]]; then
        echo "0 0 */7 * * /root/.aria2/trackers-list-aria2.sh" >> /var/spool/cron/root
    else
        echo "0 0 */7 * * /root/.aria2/trackers-list-aria2.sh" >> /var/spool/cron/crontabs/root
    fi
}

#install pyone
install_pip(){
    echo -e "${Blue}正在安装pip！${Font}"
    if [[ "${release}" = "centos" ]]; then
        yum install -y python-pip
        EXEC="$(command -v pip)"
        if [[ -z ${EXEC} ]]; then
        wget https://bootstrap.pypa.io/get-pip.py
        python get-pip.py
        fi
    else
        apt -y install python-pip
    fi
    EXEC="$(command -v pip)"
    if [[ -n ${EXEC} ]]; then
    echo -e "${Blue}pip安装成功！${Font}"
    else
    echo -e "${Red}pip安装失败！${Font}"
    exit 1
    fi

}

install_package(){
    pip2 install -r requirements.txt
}



#open firewall
firewall(){
    if [[ "${release}" = "centos" ]]; then
        firewall-cmd --zone=public --add-port=6800/tcp --permanent
        firewall-cmd --zone=public --add-port=34567/tcp --permanent
        firewall-cmd --zone=public --add-port=80/tcp --permanent
        firewall-cmd --zone=public --add-port=443/tcp --permanent
        firewall-cmd --reload
    fi
}



#set start up
start(){
        echo -e "${Blue}正在为相关应用设置开机自启！${Font}"
echo "[Unit]
Description=Aria2 server
After=network.target
Wants=network.target

[Service]
Type=simple
PIDFile=/var/run/aria2c.pid
ExecStart=/usr/bin/aria2c --conf-path=/root/.aria2/aria2.conf
RestartPreventExitStatus=23
Restart=always
User=root

[Install]
WantedBy=multi-user.target
" > '/etc/systemd/system/aria2.service'

echo "[Unit]
Description=pyone
After=network.target
Wants=network.target

[Service]
Type=simple
PIDFile=/var/run/pyone.pid
WorkingDirectory=${cur_path}
ExecStart=gunicorn -keventlet -b 0.0.0.0:34567 run:app
RestartPreventExitStatus=23
Restart=always
User=root

[Install]
WantedBy=multi-user.target
" > '/etc/systemd/system/pyone.service'

        EXEC="$(command -v gunicorn)"
        sed -i "s#gunicorn#${EXEC}#g" /etc/systemd/system/pyone.service
        systemctl start aria2 pyone
        systemctl enable aria2 pyone
}

#Complete info
info(){
    local_ip=`curl http://whatismyip.akamai.com`
    echo -e "———————————————————————————————————————"
    echo -e "${Blue}PyOne安装完成！${Font}"
    echo -e "${Blue}请通过访问：http://${local_ip}:34567 继续后面的安装${Font}"
    echo -e "${Blue}PyOne后台密码：${pyone_pass}${Font}"
    echo -e "${Blue}Aria2密匙：${aria2_pass}${Font}"
    echo -e "${Blue}常用命令：${Font}"
    echo -e "${Blue}1. 暂停PyOne: systemctl stop pyone${Font}"
    echo -e "${Blue}2. 启动PyOne: systemctl start pyone${Font}"
    echo -e "${Blue}3. 重启PyOne: systemctl restart pyone${Font}"
    echo -e "${Blue}4. 手动运行PyOne: systemctl stop pyone && gunicorn -keventlet -b 0:34567 run:app${Font}"
    echo -e "${Blue}5. 暂停Aria2: systemctl stop aria2${Font}"
    echo -e "${Blue}6. 启动Aria2: systemctl start aria2${Font}"
    echo -e "${Blue}7. 重启Aria2: systemctl restart aria2${Font}"
    echo -e "———————————————————————————————————————"
    echo -e "${Blue}PyOne交流群：864996565${Font}"
    echo -e "${Blue}PyOne交流群TG：https://t.me/joinchat/JQOOug6MY11gy_MiXTmqIA${Font}"
}

#start menu
main(){
    check_root
    check_system
    check_version
    check_service
    clear
    echo -e "———————————————————————————————————————"
    echo -e "${Blue}PyOne一键脚本 for Debian 8+ 、CentOS 7、Ubuntu 16+${Font}"
    echo -e "本脚本参考【萌鼠博客】：https://www.moerats.com/archives/806/"
    echo -e "${Blue}安装之前请确保已经在安装宝塔，并且在宝塔-软件管理已经安装MongoDB和redis${Font}"
    echo -e "———————————————————————————————————————"
    config_file
    enter
    install_depend
    install_aria2
    install_pip
    install_package
    firewall
    start
    info
}

main
