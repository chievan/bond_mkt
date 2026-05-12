<script setup>
import { ref } from 'vue'
import YieldCurveView from './views/YieldCurveView.vue'
import TradingStatusView from './views/TradingStatusView.vue'
import MarketTableView from './views/MarketTableView.vue'
import BasisMonitoringView from './views/BasisMonitoringView.vue'

// --- Configuration ---
const terms = ['1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '30Y', '50Y']
const bondTypes = ['国债', '国开债', '农发债', '口行债', '地方政府债'] // Order for the top tabs
const sheets = ['成交情况', '中债利率曲线', '期现基差', '利差', '品种利差']

const currentSheet = ref('成交情况')
const activeTab = ref('国债')
const selectedDate = ref(new Date().toISOString().split('T')[0])
const prevDate = ref('')
const oneWeekAgoDate = ref('')
const oneWeekAgoCurves = ref({})

// --- Data Generation ---
const generateMockCurve = (baseYield) => {
  return terms.map((term, index) => {
    const yieldVal = (baseYield + (index * 0.12) + (Math.random() * 0.04)).toFixed(4)
    const change = (Math.random() * 4 - 2).toFixed(2) // Non-zero change in BP
    const percentile = (0.3 + Math.random() * 0.4).toFixed(4)
    return { term, yield: yieldVal, change, percentile }
  })
}

const generateMockTable = (title, count = 15) => {
  return Array.from({ length: count }).map((_, i) => ({
    name: title + ' ' + (i + 1),
    value: (Math.random() * 3 + 1).toFixed(4),
    change: (Math.random() * 0.02 - 0.01).toFixed(4),
    percentile: (Math.random() * 1).toFixed(4)
  }))
}

// Global State
const allData = ref({
  curves: {
    '国债': generateMockCurve(1.8500),
    '国开债': generateMockCurve(2.0500),
    '农发债': generateMockCurve(2.1000),
    '口行债': generateMockCurve(2.1200),
    '地方政府债': generateMockCurve(2.2000)
  },
  '利差': generateMockTable('利差指标'),
  '品种利差': generateMockTable('品种价差'),
  '基差': generateMockTable('基差数据'),
  '成交情况': generateMockTable('成交数据', 20)
})

const fetchRealData = async (date = '') => {
    try {
        const url = date ? `http://localhost:8000/yields?date=${date}` : `http://localhost:8000/yields`
        const res = await fetch(url)
        const data = await res.json()
        if (data.curves && Object.keys(data.curves).length > 0) {
            allData.value.curves = data.curves
            if (data.date) {
                selectedDate.value = data.date
                
                // Fetch One Week Ago
                const targetDate = new Date(data.date)
                targetDate.setDate(targetDate.getDate() - 7)
                const agoStr = targetDate.toISOString().split('T')[0]
                oneWeekAgoDate.value = agoStr
                
                const agoRes = await fetch(`http://localhost:8000/yields?date=${agoStr}`)
                const agoData = await agoRes.json()
                if (agoData.curves) {
                    oneWeekAgoCurves.value = agoData.curves
                }
            }
            if (data.prev_date) {
                prevDate.value = data.prev_date
            }
            return true
        }
    } catch (e) {
        console.warn("Backend not available, using mock data")
    }
    return false
}

const syncData = async (isManual = true) => {
    // Double confirmation for any sync action that hits the API
    if (isManual) {
        const confirmed = window.confirm("确定要同步行情吗？这将消耗 iFinD API 接口点数。")
        if (!confirmed) return
    }

    // 1. Try to sync real data from backend
    try {
        const res = await fetch(`http://localhost:8000/sync?date=${selectedDate.value}`, { method: 'POST' })
        const status = await res.json()
        if (status.status === 'success') {
            await fetchRealData(selectedDate.value)
            return
        }
    } catch (e) {
        console.error("Sync failed:", e)
    }

    // 2. Fallback to Mock if real sync fails
    const dateOffset = (new Date(selectedDate.value).getTime() % 1000) / 10000
    Object.keys(allData.value.curves).forEach(k => {
        const base = k === '国债' ? 1.85 : 2.05
        allData.value.curves[k] = generateMockCurve(base + dateOffset)
    })
    sheets.slice(1).forEach(s => {
        allData.value[s] = generateMockTable(s)
    })
}

// Initial Load
import { onMounted } from 'vue'
onMounted(() => {
    fetchRealData()
})
</script>

<template>
  <div class="h-screen w-screen bg-[#020617] text-slate-300 font-sans flex overflow-hidden text-[12px]">
    
    <!-- Sidebar -->
    <aside class="w-56 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 shadow-2xl z-50">
      <div class="p-4 mb-4 flex items-center gap-2.5">
        <div class="w-7 h-7 bg-sky-600 rounded-lg flex items-center justify-center shadow-lg">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        </div>
        <div class="font-black text-base tracking-tighter text-white uppercase">Bond Hub</div>
      </div>

      <nav class="flex-1 px-2 space-y-0.5 overflow-y-auto custom-scrollbar">
        <button 
          v-for="sheet in sheets" 
          :key="sheet"
          @click="currentSheet = sheet"
          :class="[
            'w-full text-left px-3 py-2 rounded-lg transition-all flex items-center justify-between group',
            currentSheet === sheet 
              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm' 
              : 'text-slate-500 hover:bg-slate-800/40 hover:text-slate-300 border border-transparent'
          ]"
        >
          <span class="font-bold">{{ sheet }}</span>
          <div v-if="currentSheet === sheet" class="w-1 h-1 bg-sky-500 rounded-full shadow-[0_0_5px_#0ea5e9]"></div>
        </button>
      </nav>

      <div class="p-4 border-t border-slate-800">
        <div class="flex items-center gap-2 text-[10px] font-bold text-emerald-500 uppercase tracking-tight">
          <span class="w-1 h-1 bg-emerald-500 rounded-full animate-pulse"></span>
          Live Engine Active
        </div>
      </div>
    </aside>

    <!-- Main Container -->
    <div class="flex-1 flex flex-col min-w-0 bg-[#020617]">
      
      <!-- Header -->
      <header class="h-12 bg-slate-900/50 backdrop-blur-xl border-b border-slate-800 flex items-center justify-between px-6 shrink-0 z-40">
        <h1 class="text-xs font-black text-white uppercase tracking-wider">{{ currentSheet }}</h1>
        <div class="flex items-center gap-3">
          <!-- Date Picker -->
          <div class="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/></svg>
            <input 
              type="date" 
              v-model="selectedDate"
              @change="fetchRealData(selectedDate)"
              class="bg-transparent border-none text-[11px] font-bold text-slate-300 focus:outline-none focus:ring-0 [color-scheme:dark]"
            />
          </div>

          <button 
            @click="syncData"
            class="bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded-lg text-[10px] font-bold border border-slate-700 transition-all flex items-center gap-1.5 active:scale-95"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
            同步行情
          </button>
        </div>
      </header>

      <!-- View Wrapper -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-4">
        
        <!-- View: Yield Curve -->
        <YieldCurveView 
          v-if="currentSheet === '中债利率曲线'"
          :allCurves="allData.curves"
          v-model:activeTab="activeTab"
          :bondTypes="bondTypes"
          :selectedDate="selectedDate"
          :prevDate="prevDate"
        />

        <TradingStatusView
          v-if="currentSheet === '成交情况'"
          :allCurves="allData.curves"
          :oneWeekAgoCurves="oneWeekAgoCurves"
          v-model:activeTab="activeTab"
          :bondTypes="bondTypes"
          :selectedDate="selectedDate"
          :prevDate="prevDate"
          :oneWeekAgoDate="oneWeekAgoDate"
        />

        <!-- View: Basis Monitoring -->
        <BasisMonitoringView
          v-if="currentSheet === '期现基差'"
          :allCurves="allData.curves"
          :selectedDate="selectedDate"
          :prevDate="prevDate"
        />

        <!-- View: Market Tables -->
        <MarketTableView 
          v-if="currentSheet !== '中债利率曲线' && currentSheet !== '成交情况'"
          :data="allData[currentSheet]"
          :title="currentSheet"
        />

      </div>
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

:root { font-family: 'Inter', sans-serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }

.custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

body { background: #020617; margin: 0; overflow: hidden; }
</style>
