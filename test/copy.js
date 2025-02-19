/*
网络变化监控 For Quantumult X
[rewrite_local]
event-network script-path=https://raw.githubusercontent.com/yourname/yourrepo/master/network-monitor.js, tag=网络监测, enabled=true
*/

// 初始化存储
let NETWORK_CHECK = $prefs.valueForKey("NetworkCheck");
if (!NETWORK_CHECK) {
    NETWORK_CHECK = {
        'lastNetworkType': '',
        'lastNetworkState': '',
        'failCount': 0
    };
    $prefs.setValueForKey(JSON.stringify(NETWORK_CHECK), "NetworkCheck");
} else {
    NETWORK_CHECK = JSON.parse(NETWORK_CHECK);
}

// 主要检测函数
function networkCheck() {
    let currentNetworkType = $network.v4.primaryInterface;
    let currentNetworkState = $network.v4.primaryAddress ? "已连接" : "未连接";
    
    // 网络类型变化检测
    if (NETWORK_CHECK.lastNetworkType !== currentNetworkType) {
        if (currentNetworkType === 'en0') {
            $notify("网络切换提醒 🔄", "", "当前网络已切换到 WiFi");
        } else if (currentNetworkType === 'pdp_ip0') {
            $notify("网络切换提醒 🔄", "", "当前网络已切换到 蜂窝数据");
        }
        NETWORK_CHECK.lastNetworkType = currentNetworkType;
    }

    // 网络状态变化检测
    if (NETWORK_CHECK.lastNetworkState !== currentNetworkState) {
        if (currentNetworkState === "已连接") {
            $notify("网络状态提醒 ✅", "", "网络已恢复连接");
            NETWORK_CHECK.failCount = 0;
        } else {
            $notify("网络状态提醒 ❌", "", "网络连接已断开");
        }
        NETWORK_CHECK.lastNetworkState = currentNetworkState;
    }

    // 网络稳定性检测
    if (currentNetworkState === "已连接") {
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
            $prefs.setValueForKey(JSON.stringify(NETWORK_CHECK), "NetworkCheck");
        }).catch(error => {
            NETWORK_CHECK.failCount++;
            if (NETWORK_CHECK.failCount >= 3) {
                $notify("网络状态提醒 ⚠️", "", "当前网络不稳定");
                NETWORK_CHECK.failCount = 0;
            }
            $prefs.setValueForKey(JSON.stringify(NETWORK_CHECK), "NetworkCheck");
        });
    }

    $done();
}

// 执行检测
networkCheck();
