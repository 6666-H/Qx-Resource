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

// Env 类
function Env(t,e){class s{constructor(t){this.env=t}send(t,e="GET"){t="string"==typeof t?{url:t}:t;let s=this.get;return"POST"===e&&(s=this.post),new Promise((e,a)=>{s.call(this,t,(t,s,r)=>{t?a(t):e(s)})})}get(t){return this.send.call(this.env,t)}post(t){return this.send.call(this.env,t,"POST")}}return new class{constructor(t,e){this.name=t,this.http=new s(this),this.data=null,this.dataFile="box.dat",this.logs=[],this.isMute=!1,this.isNeedRewrite=!1,this.logSeparator="\n",this.encoding="utf-8",this.startTime=(new Date).getTime(),Object.assign(this,e),this.log("",`🔔${this.name}, 开始!`)}getEnv(){return"undefined"!=typeof $environment&&$environment["surge-version"]?"Surge":"undefined"!=typeof $environment&&$environment["stash-version"]?"Stash":"undefined"!=typeof module&&module.exports?"Node.js":"undefined"!=typeof $task?"Quantumult X":"undefined"!=typeof $loon?"Loon":"undefined"!=typeof $rocket?"Shadowrocket":void 0}isNode(){return"Node.js"===this.getEnv()}isQuanX(){return"Quantumult X"===this.getEnv()}isSurge(){return"Surge"===this.getEnv()}isLoon(){return"Loon"===this.getEnv()}isShadowrocket(){return"Shadowrocket"===this.getEnv()}isStash(){return"Stash"===this.getEnv()}toObj(t,e=null){try{return JSON.parse(t)}catch{return e}}toStr(t,e=null){try{return JSON.stringify(t)}catch{return e}}getjson(t,e){let s=e;const a=this.getdata(t);if(a)try{s=JSON.parse(this.getdata(t))}catch{}return s}setjson(t,e){try{return this.setdata(JSON.stringify(t),e)}catch{return!1}}getScript(t){return new Promise(e=>{this.get({url:t},(t,s,a)=>e(a))})}runScript(t,e){return new Promise(s=>{let a=this.getdata("@chavy_boxjs_userCfgs.httpapi");a=a?a.replace(/\n/g,"").trim():a;let r=this.getdata("@chavy_boxjs_userCfgs.httpapi_timeout");r=r?1*r:20,r=e&&e.timeout?e.timeout:r;const[i,o]=a.split("@"),n={url:`http://${o}/v1/scripting/evaluate`,body:{script_text:t,mock_type:"cron",timeout:r},headers:{"X-Key":i,Accept:"*/*"},timeout:r};this.post(n,(t,e,a)=>s(a))}).catch(t=>this.logErr(t))}loaddata(){if(!this.isNode())return{};{this.fs=this.fs?this.fs:require("fs"),this.path=this.path?this.path:require("path");const t=this.path.resolve(this.dataFile),e=this.path.resolve(process.cwd(),this.dataFile),s=this.fs.existsSync(t),a=!s&&this.fs.existsSync(e);if(!s&&!a)return{};{const a=s?t:e;try{return JSON.parse(this.fs.readFileSync(a))}catch(t){return{}}}}}writedata(){if(this.isNode()){this.fs=this.fs?this.fs:require("fs"),this.path=this.path?this.path:require("path");const t=this.path.resolve(this.dataFile),e=this.path.resolve(process.cwd(),this.dataFile),s=this.fs.existsSync(t),a=!s&&this.fs.existsSync(e),r=JSON.stringify(this.data);s?this.fs.writeFileSync(t,r):a?this.fs.writeFileSync(e,r):this.fs.writeFileSync(t,r)}}lodash_get(t,e,s){const a=e.replace(/\[(\d+)\]/g,".$1").split(".");let r=t;for(const t of a)if(r=Object(r)[t],void 0===r)return s;return r}lodash_set(t,e,s){return Object(t)!==t?t:(Array.isArray(e)||(e=e.toString().match(/[^.[\]]+/g)||[]),e.slice(0,-1).reduce((t,s,a)=>Object(t[s])===t[s]?t[s]:t[s]=Math.abs(e[a+1])>>0==+e[a+1]?[]:{},t)[e[e.length-1]]=s,t)}getdata(t){let e=this.getval(t);if(/^@/.test(t)){const[,s,a]=/^@(.*?)\.(.*?)$/.exec(t),r=s?this.getval(s):"";if(r)try{const t=JSON.parse(r);e=t?this.lodash_get(t,a,""):e}catch(t){e=""}}return e}setdata(t,e){let s=!1;if(/^@/.test(e)){const[,a,r]=/^@(.*?)\.(.*?)$/.exec(e),i=this.getval(a),o=a?"null"===i?null:i||"{}":"{}";try{const e=JSON.parse(o);this.lodash_set(e,r,t),s=this.setval(JSON.stringify(e),a)}catch(e){const i={};this.lodash_set(i,r,t),s=this.setval(JSON.stringify(i),a)}}else s=this.setval(t,e);return s}getval(t){return this.isSurge()||this.isLoon()||this.isStash()||this.isShadowrocket()?$persistentStore.read(t):this.isQuanX()?$prefs.valueForKey(t):this.isNode()?(this.data=this.loaddata(),this.data[t]):this.data&&this.data[t]||null}setval(t,e){return this.isSurge()||this.isLoon()||this.isStash()||this.isShadowrocket()?$persistentStore.write(t,e):this.isQuanX()?$prefs.setValueForKey(t,e):this.isNode()?(this.data=this.loaddata(),this.data[e]=t,this.writedata(),!0):this.data&&this.data[e]||null}msg(e=t,s="",a="",r){const i=t=>!t||!this.isLoon()&&this.isSurge()?t:"string"==typeof t?this.isLoon()?t:this.isQuanX()?{"open-url":t}:void 0:"object"==typeof t&&(t["open-url"]||t["media-url"])?this.isLoon()?t["open-url"]:this.isQuanX()?t:void 0:void 0;$.isMute||(this.isSurge()||this.isLoon()||this.isStash()||this.isShadowrocket()?$notification.post(e,s,a,i(r)):this.isQuanX()&&$notify(e,s,a,i(r)));let o=["","==============\ud83d\udce3\u7cfb\u7edf\u901a\u77e5\ud83d\udce3=============="];o.push(e),s&&o.push(s),a&&o.push(a),console.log(o.join("\n"))}}(t,e)}

