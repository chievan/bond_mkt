<script setup>
import { ref, onMounted, watch, shallowRef, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  allCurves: Object,
  activeTab: String,
  bondTypes: Array,
  selectedDate: String,
  prevDate: String,
  oneWeekAgoDate: String,
  oneWeekAgoCurves: Object
})

const emit = defineEmits(['update:activeTab'])

// FIXED TERMS from the image provided by user
const terms = ['1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y', '50Y']

const selectedTerm = ref('10Y')
const chartEl = ref(null)
const trendChartEl = ref(null)
const spreadChartEl = ref(null)
const chart = shallowRef(null)
const trendChart = shallowRef(null)
const spreadChart = shallowRef(null)

// Factory Default Benchmarks from User Images
const DEFAULT_BENCHMARKS = {
  '国债': {
    '1Y': '230025.IB', '2Y': '240010.IB', '3Y': '250010.IB', '5Y': '250003.IB', 
    '7Y': '250007.IB', '10Y': '250011.IB', '20Y': '2500004.IB', '30Y': '2500002.IB', '50Y': '2500003.IB'
  },
  '国开债': {
    '1Y': '210208.IB', '2Y': '250202.IB', '3Y': '240203.IB', '5Y': '250208.IB', 
    '7Y': '220210.IB', '10Y': '250215.IB', '20Y': '09230220.IB'
  },
  '农发债': {
    '1Y': '250431.IB', '2Y': '220407.IB', '3Y': '250413.IB', '5Y': '250415.IB', 
    '7Y': '230402.IB', '10Y': '250420.IB'
  },
  '口行债': {
    '1Y': '250361.IB', '2Y': '170303.IB', '3Y': '250313.IB', '5Y': '200311.IB', 
    '7Y': '220311.IB', '10Y': '240311.IB'
  },
  '地方政府债': {
    '3Y': '198898.IB', '5Y': '2371176.IB', '7Y': '2205352.IB', '10Y': '2005291.IB', 
    '15Y': '232956.IB', '20Y': '234941.IB', '30Y': '2505080.IB'
  }
}

const COMMON_SPREADS = {
  '国债': ['3Y-1Y', '5Y-3Y', '7Y-5Y', '10Y-7Y', '30Y-10Y', '50Y-30Y'],
  '国开债': ['3Y-1Y', '5Y-3Y', '7Y-5Y', '10Y-7Y'],
  '农发债': ['3Y-1Y', '5Y-3Y', '7Y-5Y', '10Y-7Y'],
  '口行债': ['3Y-1Y', '5Y-3Y', '7Y-5Y', '10Y-7Y'],
  '地方政府债': ['3Y-1Y', '5Y-3Y', '7Y-5Y', '10Y-7Y']
}

const allBenchmarks = ref({ ...DEFAULT_BENCHMARKS })
const historyData = ref({}) // { code: [records] }
const bondValuations = ref({}) // { date: { code: yield } }

const fetchHistoryFromDB = async (code) => {
    if (!code) return
    try {
        const res = await fetch(`http://localhost:8504/bond-history?code=${code}`)
        const data = await res.json()
        historyData.value[code] = data
    } catch (e) {
        console.error("Failed to fetch history from DB:", e)
    }
}

const fetchSpecificValuations = async (date) => {
    if (!date) return
    // Collect ALL benchmark codes across all bond types
    const codes = []
    Object.values(allBenchmarks.value).forEach(typeMap => {
        Object.values(typeMap).forEach(code => { if (code) codes.push(code) })
    })
    
    if (codes.length === 0) return
    try {
        const res = await fetch(`http://localhost:8504/bond-valuations-batch?codes=${codes.join(',')}&date=${date}`)
        const data = await res.json()
        bondValuations.value = { 
            ...bondValuations.value, 
            [date]: data 
        }
    } catch (e) {
        console.error("Failed to fetch specific valuations:", e)
    }
}

const format4 = (val) => {
    const num = parseFloat(val)
    return isNaN(num) ? '0.0000' : num.toFixed(4)
}

const termToYear = (t) => {
    if (t.endsWith('Y')) return parseFloat(t)
    if (t.endsWith('M')) return parseFloat(t) / 12
    return 0
}

const formatDateShort = (dateStr) => {
    if (!dateStr) return ''
    const parts = dateStr.split('-')
    if (parts.length < 3) return dateStr
    return `${parts[1]}/${parts[2]}`
}

const getTopYield = (type) => {
  const code = allBenchmarks.value[type]?.['10Y']
  const specific = bondValuations.value[props.selectedDate]?.[code]
  if (specific !== undefined) return specific.toFixed(4)

  const curve = props.allCurves[type] || []
  const point = curve.find(p => p.term === '10Y')
  return point ? parseFloat(point.yield).toFixed(4) : '--'
}

const isTopReal = (type) => {
  const code = allBenchmarks.value[type]?.['10Y']
  return bondValuations.value[props.selectedDate]?.[code] !== undefined
}

const getTopChange = (type) => {
  const curve = props.allCurves[type] || []
  const point = curve.find(p => p.term === '10Y')
  return point ? point.change : '0.00'
}

const getChangeColor = (val) => {
  const num = parseFloat(val)
  if (num > 0) return 'text-rose-500'
  if (num < 0) return 'text-emerald-500'
  return 'text-slate-500'
}

// Current data for the table, filtered by our fixed terms
const currentTableData = computed(() => {
    const curve = props.allCurves[props.activeTab] || []
    const typeBenchmarks = allBenchmarks.value[props.activeTab] || {}
    
    return terms.map(term => {
        const code = typeBenchmarks[term]
        const specificYield = bondValuations.value[props.selectedDate]?.[code]
        const specificPrevYield = bondValuations.value[props.prevDate]?.[code]
        
        const point = curve.find(p => p.term === term) || { yield: 0, prev_yield: 0, change: 0, percentile: 0.5 }
        
        // Use specific bond valuation if available, otherwise fallback to curve point
        const finalYield = specificYield !== undefined ? specificYield : point.yield
        const finalPrevYield = specificPrevYield !== undefined ? specificPrevYield : point.prev_yield
        const finalChange = specificYield !== undefined && specificPrevYield !== undefined 
            ? (specificYield - specificPrevYield) * 100 
            : point.change

        return {
            ...point,
            term,
            yield: finalYield,
            prev_yield: finalPrevYield,
            change: finalChange,
            is_real: specificYield !== undefined,
            benchmark: code || ''
        }
    })
})

const updateCharts = () => {
  if (!chart.value || !trendChart.value) return

  const latestLabel = `最新 (${props.selectedDate})`
  const agoLabel = `一周前 (${props.oneWeekAgoDate})`
  
  const data = currentTableData.value
  const agoCurve = props.oneWeekAgoCurves[props.activeTab] || []

  const latestData = data
    .filter(p => p.yield && p.yield > 0)
    .map(p => [termToYear(p.term), p.yield])
    .sort((a,b) => a[0]-b[0])
    
  const agoData = agoCurve
    .filter(p => p.yield && p.yield > 0)
    .map(p => [termToYear(p.term), p.yield])
    .sort((a,b) => a[0]-b[0])
  
  // Spread should be Latest - 1W Ago
  const spreadData = latestData.map((p, idx) => {
      const ago = agoData.find(ap => ap[0] === p[0])
      const diff = ago ? (p[1] - ago[1]) * 100 : 0
      return [p[0], diff]
  })

  const option = {
    backgroundColor: 'transparent',
    legend: {
      show: true,
      top: 0,
      right: 0,
      textStyle: { color: '#64748b', fontSize: 9 },
      itemWidth: 12,
      itemHeight: 2,
      data: [latestLabel, agoLabel, '变动 (BP)']
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      textStyle: { color: '#f1f5f9', fontSize: 10 },
      formatter: (params) => {
        if (!params || params.length === 0) return ''
        const year = params[0].value[0]
        const label = year + 'Y'
        let res = `<div class="font-bold mb-1 text-[10px] text-slate-400">${label} 成交监控</div>`
        params.forEach(p => {
          if (p.seriesType === 'line') {
            res += `<div class="flex justify-between gap-6 text-[10px] py-0.5">
              <span class="text-slate-500">${p.seriesName}:</span>
              <span class="font-mono font-bold" style="color: ${p.color}">${format4(p.value[1])}%</span>
            </div>`
          } else if (p.seriesType === 'bar') {
            res += `<div class="flex justify-between gap-6 text-[10px] py-0.5 border-t border-slate-800 mt-1 pt-1">
              <span class="text-slate-400">变动 (BP):</span>
              <span class="font-mono font-bold ${p.value[1] >= 0 ? 'text-rose-500' : 'text-emerald-500'}">
                ${p.value[1] >= 0 ? '+' : ''}${p.value[1].toFixed(2)}
              </span>
            </div>`
          }
        })
        return res
      }
    },
    grid: { left: '45', right: '45', bottom: '30', top: '40' },
    xAxis: {
      type: 'value',
      min: 0,
      max: 50,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#64748b', fontSize: 9, formatter: (v) => v + 'Y' },
      splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.1)', type: 'dashed' } }
    },
    yAxis: [
      {
        type: 'value',
        scale: true,
        boundaryGap: ['5%', '5%'],
        splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
        axisLabel: { color: '#64748b', fontSize: 9, formatter: (v) => v.toFixed(2) + '%' }
      },
      {
        type: 'value',
        name: 'BP',
        nameTextStyle: { color: '#475569', fontSize: 8 },
        splitLine: { show: false },
        axisLabel: { color: '#64748b', fontSize: 8, formatter: (v) => v + 'bp' }
      }
    ],
    series: [
      {
        name: '变动 (BP)',
        type: 'bar',
        yAxisIndex: 1,
        data: spreadData,
        barWidth: '60%',
        itemStyle: {
          color: (params) => params.value[1] >= 0 ? 'rgba(244, 63, 94, 0.4)' : 'rgba(16, 185, 129, 0.4)',
          borderRadius: [2, 2, 0, 0],
          borderColor: (params) => params.value[1] >= 0 ? 'rgba(244, 63, 94, 0.6)' : 'rgba(16, 185, 129, 0.6)',
          borderWidth: 1
        }
      },
      {
        name: latestLabel,
        data: latestData,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 1.2, shadowBlur: 8, shadowColor: 'rgba(245, 158, 11, 0.5)' },
        z: 10
      },
      {
        name: agoLabel,
        data: agoData,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 0,
        itemStyle: { color: '#475569' },
        lineStyle: { width: 0.8, type: 'dashed', opacity: 0.6 },
        z: 5
      }
    ]
  }
  chart.value.setOption(option)

  // Trend Chart (Real Data from Sync)
  const activeBenchmark = allBenchmarks.value[props.activeTab]?.[selectedTerm.value]
  const lastMonthStart = new Date()
  lastMonthStart.setMonth(lastMonthStart.getMonth() - 1)
  lastMonthStart.setDate(1)
  const lastMonthStr = lastMonthStart.toISOString().split('T')[0]

  const realTrend = (historyData.value[activeBenchmark] || [])
    .filter(r => r.date >= lastMonthStr) // Filter from 1st of last month
    .map(r => [
      r.date.split('-').slice(1).join('-'), // MM-DD
      r.yield
    ])
  
  // Fallback to mock if no real data yet
  const displayTrend = realTrend.length > 0 ? realTrend : []
  
  const trendOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.9)', formatter: '{b}: {c}%' },
    grid: { top: 40, bottom: 40, left: 50, right: 30 },
    xAxis: { type: 'category', data: displayTrend.map(d => d[0]), axisLabel: { color: '#64748b', fontSize: 9 } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: '#64748b', fontSize: 9, formatter: '{value}%' }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.1)' } } },
    series: [{ 
      name: 'Yield',
      data: displayTrend.map(d => d[1]), 
      type: 'line', smooth: true, showSymbol: false,
      areaStyle: { 
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245, 158, 11, 0.2)' },
          { offset: 1, color: 'rgba(245, 158, 11, 0)' }
        ])
      }, 
      itemStyle: { color: '#f59e0b' },
      lineStyle: { width: 1.5 }
    }]
  }
  trendChart.value.setOption(trendOption)

  // Spread Levels Chart (NEW)
  if (spreadChart.value) {
    const spreadConfigs = COMMON_SPREADS[props.activeTab] || []
    const spreadDataPoints = spreadConfigs.map(s => {
        const [t2, t1] = s.split('-')
        const p2 = data.find(d => d.term === t2)
        const p1 = data.find(d => d.term === t1)
        if (p2 && p1 && p2.yield > 0 && p1.yield > 0) {
            const level = (p2.yield - p1.yield) * 100 // Level in BP
            const prevLevel = (p2.prev_yield - p1.prev_yield) * 100
            const change = level - prevLevel
            return { name: s, level, change }
        }
        return { name: s, level: 0, change: 0 }
    }).filter(p => p.level !== 0)

    const spreadOption = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.9)' },
        grid: { top: 40, bottom: 30, left: 50, right: 50 },
        legend: { data: ['利差水平 (BP)', '较昨日变动 (BP)'], textStyle: { color: '#64748b', fontSize: 9 }, top: 0 },
        xAxis: { type: 'category', data: spreadDataPoints.map(d => d.name), axisLabel: { color: '#64748b', fontSize: 9 } },
        yAxis: [
            { type: 'value', name: 'BP', axisLabel: { color: '#64748b', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.1)' } } },
            { type: 'value', name: '变动', axisLabel: { color: '#64748b', fontSize: 9 }, splitLine: { show: false } }
        ],
        series: [
            { 
                name: '利差水平 (BP)', 
                type: 'line', 
                data: spreadDataPoints.map(d => d.level.toFixed(2)), 
                smooth: true, 
                symbol: 'circle', 
                itemStyle: { color: '#f59e0b' } 
            },
            { 
                name: '较昨日变动 (BP)', 
                type: 'bar', 
                yAxisIndex: 1, 
                data: spreadDataPoints.map(d => d.change.toFixed(2)), 
                itemStyle: { 
                    color: (p) => p.value >= 0 ? 'rgba(244, 63, 94, 0.4)' : 'rgba(16, 185, 129, 0.4)',
                    borderColor: (p) => p.value >= 0 ? 'rgba(244, 63, 94, 0.6)' : 'rgba(16, 185, 129, 0.6)',
                    borderWidth: 1
                }
            }
        ]
    }
    spreadChart.value.setOption(spreadOption)
  }
}

const initCharts = async () => {
  await nextTick()
  if (chartEl.value) chart.value = echarts.init(chartEl.value)
  if (trendChartEl.value) trendChart.value = echarts.init(trendChartEl.value)
  if (spreadChartEl.value) spreadChart.value = echarts.init(spreadChartEl.value)
  updateCharts()
}

// API Integration
const fetchBenchmarks = async () => {
    // Fetch for ALL types to populate summary cards
    for (const type of props.bondTypes) {
        try {
            const res = await fetch(`http://localhost:8504/benchmarks?bond_type=${type}`)
            const data = await res.json()
            if (Object.keys(data).length > 0) {
                allBenchmarks.value[type] = data
            }
        } catch (e) {
            console.error(`Failed to fetch benchmarks for ${type}:`, e)
        }
    }
}

const saveBenchmarks = async () => {
    try {
        await fetch(`http://localhost:8504/benchmarks/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bond_type: props.activeTab,
                benchmarks: allBenchmarks.value[props.activeTab]
            })
        })
    } catch (e) {
        console.error("Failed to save benchmarks:", e)
    }
}

const syncHistory = async (codes) => {
    if (!codes || codes.length === 0) return
    try {
        await fetch(`http://localhost:8504/sync-bond-history`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(codes)
        })
        // Fetch current term's history after sync
        const activeBenchmark = allBenchmarks.value[props.activeTab]?.[selectedTerm.value]
        if (activeBenchmark) await fetchHistoryFromDB(activeBenchmark)
        updateCharts()
    } catch (e) {
        console.error("Failed to sync history:", e)
    }
}

watch(() => selectedTerm.value, async (term) => {
    const typeMap = allBenchmarks.value[props.activeTab]
    const code = typeMap ? typeMap[term] : null
    if (code) {
        await fetchHistoryFromDB(code)
        updateCharts()
    }
})

onMounted(async () => {
  await fetchBenchmarks()
  // Fetch initial valuations for ALL benchmarks across ALL types
  await fetchSpecificValuations(props.selectedDate)
  await fetchSpecificValuations(props.prevDate)
  
  // Fetch initial history for current term
  const code = allBenchmarks.value[props.activeTab]?.[selectedTerm.value]
  if (code) await fetchHistoryFromDB(code)
  
  initCharts()
  window.addEventListener('resize', () => {
    chart.value?.resize()
    trendChart.value?.resize()
    spreadChart.value?.resize()
  })
})

watch(() => [props.selectedDate, props.prevDate, allBenchmarks.value], async ([newDate, newPrev, newBenchmarks]) => {
    if (newDate) await fetchSpecificValuations(newDate)
    if (newPrev) await fetchSpecificValuations(newPrev)
}, { deep: true })

watch(() => props.activeTab, () => {
  // No need to fetchBenchmarks here anymore as we fetch all on mount
  // but we can refresh the current history
  const code = allBenchmarks.value[props.activeTab]?.[selectedTerm.value]
  if (code) fetchHistoryFromDB(code).then(() => updateCharts())
})

watch(() => allBenchmarks.value[props.activeTab], async (newVal) => {
    if (!newVal) return
    saveBenchmarks()
    const codes = Object.values(newVal).filter(c => c && c.length > 0)
    syncHistory(codes)
}, { deep: true })

watch(() => [props.allCurves, props.oneWeekAgoCurves, props.activeTab, selectedTerm.value], () => updateCharts(), { deep: true })
</script>

<template>
  <div class="space-y-3">
    <!-- Summary Cards -->
    <section class="grid grid-cols-5 gap-2.5">
      <button 
        v-for="type in bondTypes" 
        :key="type"
        @click="$emit('update:activeTab', type)"
        :class="[
          'relative p-3 rounded-2xl border text-left transition-all group overflow-hidden',
          activeTab === type 
            ? 'bg-amber-500/10 border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.15)]' 
            : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
        ]"
      >
        <div v-if="activeTab === type" class="absolute top-0 left-0 w-full h-1 bg-amber-500"></div>
        <div class="flex flex-col gap-1">
          <div class="flex items-center justify-between text-[10px] font-black tracking-widest uppercase">
            <div class="flex items-center gap-2 text-slate-500">
              <span class="text-amber-500">10Y</span> {{ type }}
            </div>
            <span class="text-slate-600 font-bold ml-2">{{ formatDateShort(selectedDate) }}</span>
          </div>
          <div class="flex items-baseline justify-between mt-1.5">
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-black text-white tracking-tighter" :class="isTopReal(type) ? 'text-amber-400' : 'text-white'">{{ getTopYield(type) }}</span>
              <span class="text-[11px] font-bold text-slate-500 opacity-50">%</span>
              <span v-if="isTopReal(type)" class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse ml-1" title="Real Bond Data"></span>
            </div>
            <div :class="['text-xs font-bold font-mono px-2 py-0.5 rounded bg-slate-950/50', getChangeColor(getTopChange(type))]">
              {{ parseFloat(getTopChange(type)) > 0 ? '+' : '' }}{{ getTopChange(type) }}BP
            </div>
          </div>
        </div>
      </button>
    </section>

    <!-- Main Content -->
    <div class="space-y-3">
        <section class="space-y-2">
            <div class="flex items-center justify-between px-1">
                <div class="flex items-center gap-2">
                    <div class="w-1.5 h-3.5 bg-amber-500 rounded-full shadow-[0_0_8px_#f59e0b]"></div>
                    <span class="text-[11px] font-black text-white uppercase tracking-widest">{{ activeTab }} 成交情况监控</span>
                </div>
                <div class="flex items-center gap-3">
                  <button 
                    @click="syncHistory(Object.values(allBenchmarks[activeTab]))"
                    class="text-[9px] font-bold text-amber-500 bg-amber-500/5 hover:bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 uppercase tracking-widest transition-all active:scale-95"
                  >
                    更新所有标的券历史
                  </button>
                  <div class="text-[10px] text-slate-500 font-bold bg-amber-500/5 px-2 py-0.5 rounded border border-amber-500/10 uppercase tracking-widest">LIVE TRADING DATA</div>
                </div>
            </div>

            <div class="grid grid-cols-12 gap-3">
                <!-- Left Column: Table & Spread Chart -->
                <div class="col-span-12 xl:col-span-6 flex flex-col gap-3">
                    <div class="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-inner flex flex-col h-[320px]">
                        <!-- Table Header -->
                        <div class="bg-slate-900 border-b border-slate-800 flex items-center h-8 px-4">
                            <div class="w-16 font-black text-slate-500 uppercase tracking-tighter text-[9px]">关键期限</div>
                            <div class="w-20 font-black text-slate-500 uppercase tracking-tighter text-[9px]">
                              昨收 <span class="text-[8px] opacity-60">({{ formatDateShort(prevDate) }})</span>
                            </div>
                            <div class="w-20 font-black text-slate-500 uppercase tracking-tighter text-[9px]">
                              最新 <span class="text-[8px] opacity-60">({{ formatDateShort(selectedDate) }})</span>
                            </div>
                            <div class="w-20 font-black text-slate-500 uppercase tracking-tighter text-[9px]">日变动 (BP)</div>
                            <div class="flex-1 font-black text-slate-500 uppercase tracking-tighter text-[9px] pl-4">标的券</div>
                        </div>
                        <!-- Table Body (Adaptive Rows) -->
                        <div class="flex-1 flex flex-col divide-y divide-slate-800/40">
                            <div 
                                v-for="row in currentTableData" 
                                :key="row.term" 
                                @click="selectedTerm = row.term"
                                :class="[
                                    'flex-1 flex items-center px-4 hover:bg-amber-500/5 transition-all group cursor-pointer',
                                    selectedTerm === row.term ? 'bg-amber-500/10 border-l-2 border-amber-500' : ''
                                ]"
                            >
                                <div class="w-16 font-bold text-slate-400 group-hover:text-white transition-colors text-[11px]">{{ row.term }}</div>
                                <div class="w-20 font-mono text-slate-500 italic text-[11px]">{{ format4(row.prev_yield) }}</div>
                                <div class="w-20 font-mono font-bold text-[11px] flex items-center gap-1" :class="row.is_real ? 'text-amber-400' : 'text-slate-400'">
                                    {{ format4(row.yield) }}
                                    <span v-if="row.is_real" class="w-1 h-1 rounded-full bg-amber-500 animate-pulse" title="Real Bond Data"></span>
                                </div>
                                <div :class="['w-20 font-mono font-bold text-[11px]', getChangeColor(row.change)]">
                                    {{ parseFloat(row.change) > 0 ? '+' : '' }}{{ parseFloat(row.change).toFixed(2) }}
                                </div>
                                <div class="flex-1 pl-4">
                                    <input 
                                        v-model="allBenchmarks[activeTab][row.term]"
                                        @click.stop
                                        class="w-full bg-slate-950/50 border border-slate-800 rounded px-2 py-0.5 text-[11px] font-mono text-amber-500 focus:outline-none focus:border-amber-500/50 transition-all placeholder:text-slate-700"
                                        placeholder="输入代码..."
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Historical Trend (Moved to Left Column) -->
                    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-4 flex flex-col h-[320px] shadow-2xl relative group">
                        <div class="flex items-center justify-between mb-2">
                             <div class="text-[10px] font-black text-slate-500 uppercase tracking-widest">{{ selectedTerm }} {{ activeTab }} 历史走势</div>
                             <div class="text-[9px] font-bold text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded uppercase tracking-widest">Historical Trend</div>
                        </div>
                        <div ref="trendChartEl" class="flex-1 w-full"></div>
                    </div>
                </div>

                <!-- Right Column: Term Structure & Spread Chart -->
                <div class="col-span-12 xl:col-span-6 flex flex-col gap-3">
                    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-4 flex flex-col h-[320px] shadow-2xl relative group">
                        <div class="absolute top-6 right-6 flex items-center gap-2">
                            <div class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></div>
                            <span class="text-[9px] font-black text-amber-500/60 uppercase tracking-widest">LIVE TRADING</span>
                        </div>
                        <div class="text-[10px] font-black text-slate-500 uppercase mb-2 tracking-widest">{{ activeTab }} 成交期限结构</div>
                        <div ref="chartEl" class="flex-1 w-full"></div>
                    </div>

                    <!-- Spread Chart (Moved to Right Column) -->
                    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-4 flex flex-col h-[320px] shadow-2xl relative group">
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                                <div class="w-1.5 h-1.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"></div>
                                <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-widest">{{ activeTab }} 曲线利差监控</h3>
                            </div>
                        </div>
                        <div ref="spreadChartEl" class="flex-1 w-full"></div>
                    </div>
                </div>

            </div>
        </section>
    </div>
  </div>
</template>

<style scoped>
.shadow-inner { box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06); }
</style>
