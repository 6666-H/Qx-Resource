/*
网络变化监控 For Quantumult X
[rewrite_local]
event-network script-path=network-monitor.js, tag=网络监测, enabled=true
*/

// 获取网络状态
function getNetworkInfo() {
    return new Promise((resolve) => {
        $httpClient.get('http://ip-api.com/json', function(error, response, data) {
            if (error) {
                resolve({
                    networkType: 'unknown',
                    isConnected: false
                });
                return;
            }
            try {
                let info = JSON.parse(data);
                resolve({
                    networkType: info.mobile ? 'cellular' : 'wifi',
                    isConnected: true,
                    ip: info.query
                });
            } catch (e) {
                resolve({
                    networkType: 'unknown',
                    isConnected: false
                });
            }
        });
    });
}

// 网络状态检查
async function networkCheck() {
    let NETWORK_CHECK = $prefs.valueForKey("NetworkCheck");
    if (!NETWORK_CHECK) {
        NETWORK_CHECK = {
            'lastNetworkType': '',
            'lastNetworkState': '',
            'failCount': 0
        };
    } else {
        NETWORK_CHECK = JSON.parse(NETWORK_CHECK);
    }

    // 获取当前网络状态
    let currentNetwork = await getNetworkInfo();
    
    // 网络类型变化检测
    if (NETWORK_CHECK.lastNetworkType !== currentNetwork.networkType) {
        if (currentNetwork.networkType === 'wifi') {
            $notify("网络切换提醒 🔄", "", "当前网络已切换到 WiFi");
        } else if (currentNetwork.networkType === 'cellular') {
            $notify("网络切换提醒 🔄", "", "当前网络已切换到 蜂窝数据");
        }
        NETWORK_CHECK.lastNetworkType = currentNetwork.networkType;
    }

    // 网络连接状态检测
    if (NETWORK_CHECK.lastNetworkState !== currentNetwork.isConnected) {
        if (currentNetwork.isConnected) {
            $notify("网络状态提醒 ✅", "", "网络已恢复连接");
            NETWORK_CHECK.failCount = 0;
        } else {
            $notify("网络状态提醒 ❌", "", "网络连接已断开");
        }
        NETWORK_CHECK.lastNetworkState = currentNetwork.isConnected;
    }

    // 网络稳定性检测
    if (currentNetwork.isConnected) {
        $task.fetch({
            url: "http://www.gstatic.com/generate_204",
            timeout: 3000
        }).then(response => {
            if (response.statusCode === 204) {
                if (NETWORK_CHECK.failCount > 0) {
                    $notify("网络状态提醒 🌟", "", "网络恢复正常");
                    NETWORK_CHECK.failCount = 0;
                }
            } else {
                NETWORK_CHECK.failCount++;
                if (NETWORK_CHECK.failCount >= 3) {
                    $notify("网络状态提醒 ⚠️", "", "当前网络不稳定");
                    NETWORK_CHECK.failCount = 0;
                }
            }
        }).catch(error => {
            NETWORK_CHECK.failCount++;
            if (NETWORK_CHECK.failCount >= 3) {
                $notify("网络状态提醒 ⚠️", "", "当前网络不稳定");
                NETWORK_CHECK.failCount = 0;
            }
        }).finally(() => {
            $prefs.setValueForKey(JSON.stringify(NETWORK_CHECK), "NetworkCheck");
        });
    }
}

// 主函数
function main() {
    networkCheck().then(() => $done());
}

// 执行主函数
main();
