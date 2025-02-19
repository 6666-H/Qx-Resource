const NAME = 'network-info'
const $ = new Env(NAME)

// 网络状态相关变量
let lastNetworkType = '' 
let lastWifiName = ''
let lastNetworkStatus = true 

// 从持久化存储读取上次的网络状态
try {
  const savedState = $.getjson('lastNetworkState')
  if (savedState) {
    lastNetworkType = savedState.type || ''
    lastWifiName = savedState.wifi || ''
    lastNetworkStatus = savedState.connected || true
  }
} catch (e) {
  $.logErr('读取保存的网络状态失败:', e)
}

let arg
if (typeof $argument != 'undefined') {
  arg = Object.fromEntries($argument.split('&').map(item => item.split('=')))
} else {
  arg = {}
}

// 获取网络状态的函数
async function getNetworkInfo() {
  let networkType = ''
  let wifiName = ''
  let isConnected = false
  let cellularType = ''

  if (typeof $network !== 'undefined') {
    // Surge/Loon 环境
    const wifi = $.lodash_get($network, 'wifi')
    const v4 = $.lodash_get($network, 'v4')
    const v6 = $.lodash_get($network, 'v6')
    const cellular = $.lodash_get($network, 'cellular')
    
    isConnected = !!(wifi?.ssid || v4?.primaryAddress || v6?.primaryAddress)
    
    if (wifi?.ssid) {
      networkType = 'WiFi'
      wifiName = wifi.ssid
    } else if (v4?.primaryAddress || v6?.primaryAddress) {
      networkType = 'Cellular'
      cellularType = cellular?.type || ''
    }
  } else if (typeof $environment !== 'undefined') {
    // QX 环境
    const network = $.lodash_get($environment, 'network')
    isConnected = network !== 'NO-NETWORK'
    
    if (network === 'WIFI') {
      networkType = 'WiFi'
      wifiName = $.lodash_get($environment, 'ssid')
    } else if (network === 'CELLULAR') {
      networkType = 'Cellular'
    }
  }

  return {
    networkType,
    wifiName, 
    isConnected,
    cellularType
  }
}

// 格式化网络类型显示
function formatNetworkType(type, cellular) {
  if (type === 'WiFi') return 'WiFi'
  if (type === 'Cellular') {
    if (cellular) {
      return cellular.toUpperCase()
    }
    return '蜂窝网络'
  }
  return '未知'
}
!(async () => {
  // 获取当前网络状态
  const { networkType, wifiName, isConnected, cellularType } = await getNetworkInfo()
  
  // 保存当前网络状态
  $.setjson({
    type: networkType,
    wifi: wifiName,
    connected: isConnected
  }, 'lastNetworkState')
  
  // 检测网络状态变化
  if (isConnected !== lastNetworkStatus) {
    if (isConnected) {
      const currentType = formatNetworkType(networkType, cellularType)
      const detail = networkType === 'WiFi' ? `WiFi: ${wifiName || '未知'}` : currentType
      await notify('网络已连接 🟢', '', detail)
    } else {
      await notify('网络已断开 🔴', '', '请检查网络设置')
      $.done()
      return
    }
  }
  
  // 检测网络类型变化
  if (networkType !== lastNetworkType) {
    const newType = formatNetworkType(networkType, cellularType)
    const oldType = formatNetworkType(lastNetworkType)
    if (networkType === 'WiFi') {
      await notify('网络切换 🔁', '', `${oldType} → WiFi: ${wifiName || '未知'}`)
    } else if (networkType === 'Cellular') {
      await notify('网络切换 🔁', '', `${oldType} → ${newType}`)
    }
  } else if (networkType === 'WiFi' && wifiName !== lastWifiName) {
    // WiFi 名称变化
    await notify('WiFi 切换 🔁', '', `${lastWifiName || '未知'} → ${wifiName || '未知'}`)
  }
  
  // 更新上一次的状态
  lastNetworkStatus = isConnected
  lastNetworkType = networkType
  lastWifiName = wifiName

  // 如果没有网络连接,直接结束
  if (!isConnected) {
    $.done()
    return
  }

  // 延迟检测
  if ($.lodash_get(arg, 'TYPE') === 'EVENT') {
    const eventDelay = parseFloat($.lodash_get(arg, 'EVENT_DELAY') || 3)
    $.log(`网络变化, 等待 ${eventDelay} 秒后开始查询`)
    if (eventDelay) {
      await $.wait(1000 * eventDelay)
    }
  }

  if (isTile()) {
    await notify('网络信息', '面板', '开始查询')
  }

  // 获取网络详细信息
  let SSID = ''
  let LAN = ''
  let LAN_IPv4 = ''
  let LAN_IPv6 = ''

  if (typeof $network !== 'undefined') {
    const v4 = $.lodash_get($network, 'v4.primaryAddress')
    const v6 = $.lodash_get($network, 'v6.primaryAddress')
    if ($.lodash_get(arg, 'SSID') == 1) {
      SSID = $.lodash_get($network, 'wifi.ssid')
    }
    if (v4 && $.lodash_get(arg, 'LAN') == 1) {
      LAN_IPv4 = v4
    }
    if (v6 && $.lodash_get(arg, 'LAN') == 1 && $.lodash_get(arg, 'IPv6') == 1) {
      LAN_IPv6 = v6
    }
  } else if (typeof $config !== 'undefined') {
    try {
      let conf = $config.getConfig()
      conf = JSON.parse(conf)
      if ($.lodash_get(arg, 'SSID') == 1) {
        SSID = $.lodash_get(conf, 'ssid')
      }
    } catch (e) {}
  }

  // 格式化显示信息
  if (LAN_IPv4 || LAN_IPv6) {
    LAN = ['LAN:', LAN_IPv4, LAN_IPv6].filter(i => i).join(' ')
  }
  if (LAN) {
    LAN = `${LAN}\n\n`
  }
  if (SSID) {
    SSID = `SSID: ${SSID}\n\n`
  } else {
    SSID = ''
  }

  // 更新面板显示
  title = networkType === 'WiFi' ? `WiFi: ${wifiName}` : formatNetworkType(networkType, cellularType)
  content = `${SSID}${LAN}连接状态: ${isConnected ? '已连接 🟢' : '未连接 🔴'}\n网络类型: ${formatNetworkType(networkType, cellularType)}`

  if (!isInteraction()) {
    content = `${content}\n更新时间: ${new Date().toTimeString().split(' ')[0]}`
  }

  // 发送通知
  if (isTile()) {
    await notify('网络信息', '面板', '查询完成')
  } else if (!isPanel()) {
    await notify(title, '', content)
  }

})()
.catch(async e => {
  $.logErr(e)
  const msg = `${$.lodash_get(e, 'message') || $.lodash_get(e, 'error') || e}`
  await notify('网络信息 ❌', '', msg)
})
.finally(() => {
  $.done()
})
// 辅助函数部分

// HTTP 请求函数
async function http(opt = {}) {
  const TIMEOUT = parseFloat(opt.timeout || $.lodash_get(arg, 'TIMEOUT') || 5)
  const RETRIES = parseFloat(opt.retries || $.lodash_get(arg, 'RETRIES') || 1)
  const RETRY_DELAY = parseFloat(opt.retry_delay || $.lodash_get(arg, 'RETRY_DELAY') || 1)

  let timeout = TIMEOUT + 1
  timeout = $.isSurge() ? timeout : timeout * 1000

  let count = 0
  const fn = async () => {
    try {
      if (TIMEOUT) {
        return await Promise.race([
          $.http.get({ ...opt, timeout }),
          new Promise((_, reject) => setTimeout(() => reject(new Error('HTTP TIMEOUT')), TIMEOUT * 1000)),
        ])
      }
      return await $.http.get(opt)
    } catch (e) {
      if (count < RETRIES) {
        count++
        $.log(`第 ${count} 次请求失败: ${e.message || e}, 等待 ${RETRY_DELAY}s 后重试`)
        await $.wait(RETRY_DELAY * 1000)
        return await fn()
      }
    }
  }
  return await fn()
}

// 解析查询字符串
function parseQueryString(url) {
  const queryString = url.split('?')[1]
  const regex = /([^=&]+)=([^&]*)/g
  const params = {}
  let match

  while ((match = regex.exec(queryString))) {
    const key = decodeURIComponent(match[1])
    const value = decodeURIComponent(match[2])
    params[key] = value
  }

  return params
}

// 环境判断函数
function isRequest() {
  return typeof $request !== 'undefined'
}

function isPanel() {
  return $.isSurge() && typeof $input != 'undefined' && $.lodash_get($input, 'purpose') === 'panel'
}

function isTile() {
  return $.isStash() && 
    ((typeof $script != 'undefined' && $.lodash_get($script, 'type') === 'tile') || 
    $.lodash_get(arg, 'TYPE') === 'TILE')
}

function isInteraction() {
  return ($.isQuanX() && 
    typeof $environment != 'undefined' && 
    $.lodash_get($environment, 'executor') === 'event-interaction') ||
    ($.isLoon() && 
    typeof $environment != 'undefined' && 
    $.lodash_get($environment, 'params.node'))
}

// 通知函数
async function notify(title, subt, desc, opts) {
  if ($.lodash_get(arg, 'TYPE') === 'EVENT' || $.lodash_get(arg, 'notify') == 1) {
    $.msg(title, subt, desc, opts)
  } else {
    $.log('🔕', title, subt, desc, opts)
  }
}

// 网络类型检查
function isIPv6(ip) {
  return ip.includes(':')
}

// 遮罩处理函数
function maskIP(ip) {
  if (!ip) return ''
  if (isIPv6(ip)) {
    return ip.replace(/(?:\w{4}:){3}\w{4}/, '****:****:****:****')
  }
  return ip.replace(/\d+\.\d+\.\d+\.(\d+)/, '***.$1')
}

function maskAddr(addr) {
  if (!addr) return ''
  return addr
    .replace(/[\u4e00-\u9fa5]{2,}/g, str => {
      if (str.length > 2) {
        return str[0] + '*'.repeat(str.length - 2) + str[str.length - 1]
      }
      return str
    })
    .replace(/[a-zA-Z]{2,}/g, str => {
      if (str.length > 2) {
        return str[0] + '*'.repeat(str.length - 2) + str[str.length - 1]
      }
      return str
    })
}

function Env(name) {
  // 日志函数
  this.log = (...args) => {
    if (args.length > 0) {
      this.logs = [...this.logs, ...args]
    }
    console.log(args.join(this.logSeparator))
  }

  // 错误日志
  this.logErr = (err, msg) => {
    this.log('', `❗️${this.name}, 错误!`, err)
  }

  this.name = name
  this.logs = []
  this.isMute = false
  this.isNeedRewrite = false
  this.logSeparator = '\n'
  this.startTime = new Date().getTime()
  this.log('', `🔔 ${this.name}, 开始!`)

  // 获取环境
  this.getEnv = () => {
    if (typeof $environment !== 'undefined') {
      if ($environment['surge-version']) return 'Surge'
      if ($environment['stash-version']) return 'Stash'
    }
    if (typeof module !== 'undefined') return 'Node.js'
    if (typeof $task !== 'undefined') return 'Quantumult X'
    if (typeof $loon !== 'undefined') return 'Loon'
    if (typeof $rocket !== 'undefined') return 'Shadowrocket'
    return 'unknown'
  }

  // 环境判断
  this.isNode = () => this.getEnv() === 'Node.js'
  this.isQuanX = () => this.getEnv() === 'Quantumult X'
  this.isSurge = () => this.getEnv() === 'Surge'
  this.isLoon = () => this.getEnv() === 'Loon'
  this.isShadowrocket = () => this.getEnv() === 'Shadowrocket'
  this.isStash = () => this.getEnv() === 'Stash'

  // 数据处理
  this.toObj = (str, defaultValue = null) => {
    try {
      return JSON.parse(str)
    } catch {
      return defaultValue
    }
  }

  this.toStr = (obj, defaultValue = null) => {
    try {
      return JSON.stringify(obj)
    } catch {
      return defaultValue
    }
  }

  // 数据存储
  this.getjson = (key, defaultValue) => {
    let val = this.getdata(key)
    if (!val) return defaultValue
    try {
      return JSON.parse(val)
    } catch {
      return defaultValue
    }
  }

  this.setjson = (val, key) => {
    try {
      return this.setdata(JSON.stringify(val), key)
    } catch {
      return false
    }
  }

  // 数据获取与存储
  this.getdata = (key) => {
    if (this.isSurge() || this.isLoon() || this.isStash() || this.isShadowrocket()) {
      return $persistentStore.read(key)
    } else if (this.isQuanX()) {
      return $prefs.valueForKey(key)
    } else {
      return null
    }
  }

  this.setdata = (val, key) => {
    if (this.isSurge() || this.isLoon() || this.isStash() || this.isShadowrocket()) {
      return $persistentStore.write(val, key)
    } else if (this.isQuanX()) {
      return $prefs.setValueForKey(val, key)
    } else {
      return false
    }
  }

  // HTTP 请求
  this.get = (opts) => {
    return new Promise((resolve, reject) => {
      if (this.isQuanX()) {
        $task.fetch(opts).then(
          response => {
            resolve(response)
          },
          reason => {
            reject(reason)
          }
        )
      } else if (this.isSurge() || this.isLoon() || this.isStash() || this.isShadowrocket()) {
        $httpClient.get(opts, (err, resp, body) => {
          if (err) reject(err)
          else resolve({ status: resp.status, headers: resp.headers, body })
        })
      }
    })
  }

  // 通知
  this.msg = (title = name, subt = '', desc = '', opts = {}) => {
    if (!this.isMute) {
      if (this.isSurge() || this.isLoon() || this.isStash() || this.isShadowrocket()) {
        $notification.post(title, subt, desc, opts)
      } else if (this.isQuanX()) {
        $notify(title, subt, desc, opts)
      }
    }
    this.log('', '==============📣系统通知📣==============')
    this.log(title)
    if (subt) this.log(subt)
    if (desc) this.log(desc)
  }

  this.done = (val = {}) => {
    const endTime = new Date().getTime()
    const costTime = (endTime - this.startTime) / 1000
    this.log('', `🔔 ${this.name}, 结束! 🕛 ${costTime} 秒`)
    if (this.isSurge() || this.isQuanX() || this.isLoon() || this.isStash() || this.isShadowrocket()) {
      $done(val)
    }
  }
}

