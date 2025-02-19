// Network Monitor for Loon
// Author: Modified by Your Name

const NAME = 'network-monitor'
const TITLE = '网络状态变更'

// 信号强度等级
const SIGNAL_LEVELS = {
    EXCELLENT: '很好 😁',
    GOOD: '良好 😊',
    FAIR: '一般 😐',
    POOR: '较差 😟',
    BAD: '很差 😫'
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

// 主函数
try {
    console.log('==================== 开始监控网络状态 ====================')
    
    // 获取上次保存的状态
    const lastState = $persistentStore.read(NAME)
    const lastNetworkState = lastState ? JSON.parse(lastState) : {
        type: '',
        ssid: '',
        running_model: ''
    }
    
    // 获取当前配置
    const config = JSON.parse($config.getConfig())
    console.log('获取到的配置:', JSON.stringify(config, null, 2))
    
    // 构建当前状态
    let currentState = {
        type: 'unknown',
        ssid: '',
        running_model: config.running_model
    }
    
    // 确定网络类型和详情
    if (config.ssid) {
        currentState.type = 'WiFi'
        currentState.ssid = config.ssid
        currentState.details = `WiFi: ${config.ssid}`
    } else {
        currentState.type = 'Cellular'
        currentState.details = '蜂窝数据'
    }
    
    // 获取运行模式
    let modeText = ''
    switch(config.running_model) {
        case 0:
            modeText = '全局直连'
            break
        case 1:
            modeText = '分流模式'
            break
        case 2:
            modeText = '全局代理'
            break
        default:
            modeText = '未知模式'
    }
    
    console.log('当前状态:', JSON.stringify(currentState, null, 2))
    console.log('上次状态:', JSON.stringify(lastNetworkState, null, 2))

    // 检查状态变化
    if (lastNetworkState.type !== currentState.type || 
        lastNetworkState.ssid !== currentState.ssid ||
        lastNetworkState.running_model !== currentState.running_model) {
        
        let title = TITLE
        let subtitle = ''
        let body = []

        // 网络类型变化
        if (lastNetworkState.type !== currentState.type || 
            lastNetworkState.ssid !== currentState.ssid) {
            
            if (currentState.type === 'WiFi') {
                subtitle = `已切换至 WiFi: ${currentState.ssid}`
            } else if (currentState.type === 'Cellular') {
                subtitle = '已切换至蜂窝数据'
            } else {
                subtitle = '网络状态未知'
            }
        }

        // 运行模式变化
        if (lastNetworkState.running_model !== currentState.running_model) {
            body.push(`当前模式: ${modeText}`)
        }

        // 添加当前策略信息
        if (config.global_proxy) {
            body.push(`全局策略: ${config.global_proxy}`)
        }
        
        if (config.ssid) {
            body.push(`当前 WiFi: ${config.ssid}`)
        }

        // 发送通知
        $notification.post(
            title, 
            subtitle || '网络状态更新', 
            body.join('\n') || '网络环境已变更'
        )
        
        // 保存新状态
        $persistentStore.write(JSON.stringify(currentState), NAME)
    }
    
    console.log('==================== 监控结束 ====================')
} catch (e) {
    console.log('❌ 发生错误:', e)
    $notification.post(NAME, '❌ 执行错误', e.message || JSON.stringify(e))
} finally {
    $done()
}
