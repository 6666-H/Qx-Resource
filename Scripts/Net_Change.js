// Network Monitor for Loon & QuanX
// Author: Modified by Your Name

const NAME = 'network-monitor'
const TITLE = '网络状态变更'

// 环境判断
const isLoon = typeof $loon !== 'undefined'
const isQuanX = typeof $task !== 'undefined'

// 统一接口
const getStore = {
    read: (key) => {
        if (isQuanX) return $prefs.valueForKey(key)
        if (isLoon) return $persistentStore.read(key)
    },
    write: (value, key) => {
        if (isQuanX) return $prefs.setValueForKey(value, key)
        if (isLoon) return $persistentStore.write(value, key)
    }
}

const notify = (title, subtitle, message, url) => {
    if (isQuanX) $notify(title, subtitle, message, { "open-url": url })
    if (isLoon) $notification.post(title, subtitle, message, url)
}

const log = console.log

// 信号强度等级
const SIGNAL_LEVELS = {
    EXCELLENT: '很好 😁',
    GOOD: '良好 😊',
    FAIR: '一般 😐',
    POOR: '较差 😟',
    BAD: '很差 😫'
}

// 网络制式的映射关系
const RADIO_TYPES = {
    '5g': '5G',
    '4g': '4G',
    '3g': '3G',
    '2g': '2G',
    'wifi': 'WiFi',
    'unknown': '未知',
    'cellular': '蜂窝数据'
}

// 评估信号强度
function evaluateSignalStrength(strength) {
    if (typeof strength !== 'number') return SIGNAL_LEVELS.FAIR;
    if (strength >= -50) return SIGNAL_LEVELS.EXCELLENT;
    if (strength >= -65) return SIGNAL_LEVELS.GOOD;
    if (strength >= -75) return SIGNAL_LEVELS.FAIR;
    if (strength >= -85) return SIGNAL_LEVELS.POOR;
    return SIGNAL_LEVELS.BAD;
}

// 获取运行模式文本
function getRunningModeText(mode) {
    switch(mode) {
        case 0:
            return '全局直连'
        case 1:
            return '分流模式'
        case 2:
            return '全局代理'
        default:
            return '未知模式'
    }
}

// 获取网络状态
async function getNetworkState() {
    let currentState = {
        type: 'unknown',
        ssid: '',
        modeText: ''
    }

    try {
        if (isLoon) {
            // Loon 环境
            const config = JSON.parse($config.getConfig())
            currentState.ssid = config.ssid || ''
            currentState.type = config.ssid ? 'wifi' : 'cellular'
            currentState.modeText = getRunningModeText(config.running_model)
            currentState.proxyMode = config.running_model
            if (config.global_proxy) {
                currentState.globalProxy = config.global_proxy
            }
        } else if (isQuanX) {
            // QuanX 环境
            const networkInfo = $network
            if (networkInfo.wifi) {
                currentState.type = 'wifi'
                currentState.ssid = networkInfo.wifi.ssid
                currentState.bssid = networkInfo.wifi.bssid
            } else if (networkInfo.cellular) {
                currentState.type = 'cellular'
                currentState.radio = networkInfo.cellular.radio
                currentState.carrier = networkInfo.cellular.carrier
            }
        }
    } catch (e) {
        log('获取网络状态出错:', e)
    }

    return currentState
}

// 主函数
!(async () => {
    try {
        log('==================== 开始监控网络状态 ====================')
        
        // 获取上次保存的状态
        const lastState = getStore.read(NAME)
        const lastNetworkState = lastState ? JSON.parse(lastState) : {
            type: '',
            ssid: '',
            proxyMode: -1
        }
        
        // 获取当前状态
        const currentState = await getNetworkState()
        
        log('当前状态:', JSON.stringify(currentState, null, 2))
        log('上次状态:', JSON.stringify(lastNetworkState, null, 2))

        // 检查状态变化
        if (lastNetworkState.type !== currentState.type || 
            lastNetworkState.ssid !== currentState.ssid ||
            lastNetworkState.proxyMode !== currentState.proxyMode) {
            
            let title = TITLE
            let subtitle = ''
            let body = []

            // 网络类型变化
            if (lastNetworkState.type !== currentState.type || 
                lastNetworkState.ssid !== currentState.ssid) {
                
                if (currentState.type === 'wifi') {
                    subtitle = `已切换至 WiFi: ${currentState.ssid}`
                } else if (currentState.type === 'cellular') {
                    subtitle = `已切换至${currentState.radio ? RADIO_TYPES[currentState.radio] : '蜂窝数据'}`
                    if (currentState.carrier) {
                        body.push(`运营商: ${currentState.carrier}`)
                    }
                } else {
                    subtitle = '网络状态未知'
                }
            }

            // 运行模式变化（仅 Loon）
            if (isLoon && lastNetworkState.proxyMode !== currentState.proxyMode) {
                body.push(`当前模式: ${currentState.modeText}`)
            }

            // 添加额外信息
            if (currentState.globalProxy) {
                body.push(`全局策略: ${currentState.globalProxy}`)
            }
            
            if (currentState.ssid) {
                body.push(`当前 WiFi: ${currentState.ssid}`)
            }

            // 发送通知
            notify(
                title, 
                subtitle || '网络状态更新', 
                body.join('\n') || '网络环境已变更'
            )
            
            // 保存新状态
            getStore.write(JSON.stringify(currentState), NAME)
        }
        
        log('==================== 监控结束 ====================')
    } catch (e) {
        log('❌ 发生错误:', e)
        notify(NAME, '❌ 执行错误', e.message || JSON.stringify(e))
    } finally {
        $done()
    }
})()
