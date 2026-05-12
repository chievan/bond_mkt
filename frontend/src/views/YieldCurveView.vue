<script setup>
import { ref, onMounted, watch, shallowRef, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  allCurves: Object,
  activeTab: String,
  bondTypes: Array,
  selectedDate: String,
  prevDate: String
})

const emit = defineEmits(['update:activeTab'])

// DOM Refs
// 21 Professional Tenors
const terms = ['0Y', '1M', '2M', '3M', '6M', '9M', '1Y', '2Y', '3Y', '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', '10Y', '15Y', '20Y', '30Y', '40Y', '50Y']

const selectedTerm = ref('10Y')
const historyData = ref([])

const format4 = (val) => {
    const num = parseFloat(val)
    return isNaN(num) ? '-' : num.toFixed(4)
}

const termToYear = (t) => {
    if (t.endsWith('Y')) return parseFloat(t)
    if (t.endsWith('M')) return parseFloat(t) / 12
    return 0
}

const getTopYield = (type) => {
  const curve = props.allCurves[type] || []
  const point = curve.find(p => p.term === '10Y')
  return point ? parseFloat(point.yield).toFixed(4) : '--'
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

const getOption = (name, currentData, yesterdayData, color) => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(15, 23, 42, 0.95)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    textStyle: { color: '#f1f5f9', fontSize: 10 },
    formatter: (params) => {
      const year = params[0].value[0]
      const label = year < 1 ? Math.round(year * 12) + 'M' : Math.round(year) + 'Y'
      let res = `<div class="font-bold mb-1 text-[10px]">${label}</div>`
      params.forEach(p => {
        res += `<div class="flex justify-between gap-4 text-[10px] py-0.5">
          <span class="text-slate-400">${p.seriesName}:</span>
          <span class="font-mono ${p.seriesName === '最新' ? 'text-sky-400' : 'text-slate-500'}">${parseFloat(p.value[1]).toFixed(4)}%</span>
        </div>`
      })
      return res
    }
  },
  legend: {
    right: 10,
    top: 0,
    textStyle: { color: '#64748b', fontSize: 9 },
    itemWidth: 10,
    itemHeight: 2
  },
  grid: { left: '45', right: '25', bottom: '30', top: '30' },
  xAxis: {
    type: 'value',
    min: 0,
    max: 50,
    axisLine: { lineStyle: { color: '#334155' } },
    axisLabel: { 
        color: '#64748b', 
        fontSize: 9,
        formatter: (v) => v + 'Y'
    },
    splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } }
  },
  yAxis: {
    type: 'value',
    scale: true,
    splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
    axisLabel: { color: '#64748b', fontSize: 9, formatter: (v) => v.toFixed(2) }
  },
  series: [
    {
      name: '最新',
      data: currentData,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: color },
      lineStyle: { width: 2 },
      connectNulls: true,
      z: 10
    },
    {
      name: '昨收',
      data: yesterdayData,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      itemStyle: { color: '#475569' },
      lineStyle: { width: 1.5, type: 'dashed', opacity: 0.6 },
      connectNulls: true,
      z: 5
    }
  ]
})

const multiCurveData = ref([])

const fetchMultiCurve = async () => {
    try {
        // Fetch 6 days to get Latest (index 0) and 5-days-ago (index 5)
        const resp = await fetch(`http://${window.location.hostname}:8504/yields/multi-history?bond_type=${props.activeTab}&limit=6`)
        multiCurveData.value = await resp.json()
        updateMainChart()
    } catch (e) {
        console.error("Multi-curve fetch failed:", e)
    }
}

const updateMainChart = () => {
    if (!chart.value || !multiCurveData.value.length) return
    
    // We only want to show the latest (index 0) and the 5th day before it (last index in our fetch)
    const latestDay = multiCurveData.value[0]
    const compareDay = multiCurveData.value.length > 1 ? multiCurveData.value[multiCurveData.value.length - 1] : null
    
    const displayDays = [latestDay]
    if (compareDay) displayDays.push(compareDay)

    const series = displayDays.map((day, index) => {
        const points = day.points
            .map(p => [termToYear(p.term), p.yield])
            .sort((a, b) => a[0] - b[0])

        const isLatest = index === 0
        return {
            name: isLatest ? '最新 (' + day.date + ')' : '5日前 (' + day.date + ')',
            data: points,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: isLatest ? 4 : 0,
            itemStyle: { color: isLatest ? '#38bdf8' : '#475569' },
            lineStyle: { 
                width: isLatest ? 1.2 : 0.8, 
                type: isLatest ? 'solid' : 'dashed',
                opacity: isLatest ? 1 : 0.5,
                shadowBlur: isLatest ? 8 : 0,
                shadowColor: isLatest ? 'rgba(56, 189, 248, 0.5)' : 'transparent'
            },
            connectNulls: true,
            z: isLatest ? 10 : 5
        }
    })

    // Calculate Spread (Latest - 5d) in BP
    const spreadData = []
    if (latestDay && compareDay) {
        const latestPoints = latestDay.points.map(p => [termToYear(p.term), p.yield]).sort((a, b) => a[0] - b[0])
        const oldPoints = compareDay.points.map(p => [termToYear(p.term), p.yield]).sort((a, b) => a[0] - b[0])
        
        latestPoints.forEach(lp => {
            const op = oldPoints.find(p => p[0] === lp[0])
            if (op) {
                spreadData.push([lp[0], (lp[1] - op[1]) * 100])
            }
        })
    }

    chart.value.setOption({
        legend: {
            show: true,
            top: 0,
            right: 0,
            textStyle: { color: '#64748b', fontSize: 9 },
            itemWidth: 12,
            itemHeight: 2,
            data: [...series.map(s => s.name), '变动 (BP)']
        },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            textStyle: { color: '#f1f5f9', fontSize: 10 },
            formatter: (params) => {
                const year = params[0].value[0]
                const label = year < 1 ? Math.round(year * 12) + 'M' : Math.round(year) + 'Y'
                let res = `<div class="font-bold mb-1 text-[10px] text-slate-400">${label} 综合分析</div>`
                params.forEach(p => {
                    if (p.seriesType === 'line') {
                        res += `<div class="flex justify-between gap-6 text-[10px] py-0.5">
                            <span class="text-slate-500">${p.seriesName}:</span>
                            <span class="font-mono font-bold" style="color: ${p.color}">${parseFloat(p.value[1]).toFixed(4)}%</span>
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
                name: '收益率',
                nameTextStyle: { color: '#475569', fontSize: 9 },
                scale: true,
                boundaryGap: ['5%', '5%'],
                splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
                axisLabel: { color: '#64748b', fontSize: 9, formatter: (v) => v.toFixed(2) + '%' }
            },
            {
                type: 'value',
                name: '变动 (BP)',
                nameTextStyle: { color: '#475569', fontSize: 9 },
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
                    color: (params) => params.value[1] >= 0 
                        ? 'rgba(244, 63, 94, 0.3)' 
                        : 'rgba(16, 185, 129, 0.3)',
                    borderRadius: [2, 2, 0, 0],
                    borderColor: (params) => params.value[1] >= 0 
                        ? 'rgba(244, 63, 94, 0.5)' 
                        : 'rgba(16, 185, 129, 0.5)',
                    borderWidth: 1
                }
            },
            ...series.map(s => ({ ...s, yAxisIndex: 0 }))
        ]
    }, true)
}

const chartEl = ref(null)
const trendChartEl = ref(null)
const chart = shallowRef(null)
const trendChart = shallowRef(null)

const fetchHistory = async () => {
    try {
        const resp = await fetch(`http://${window.location.hostname}:8504/history-yields?bond_type=${props.activeTab}&term=${selectedTerm.value}`)
        historyData.value = await resp.json()
        updateTrendChart()
    } catch (e) {
        console.error("History fetch failed:", e)
    }
}

const updateTrendChart = () => {
    if (!trendChart.value || !historyData.value.length) return
    trendChart.value.setOption({
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            textStyle: { color: '#f1f5f9', fontSize: 10 }
        },
        grid: { left: '45', right: '15', bottom: '30', top: '30' },
        xAxis: {
            type: 'category',
            data: historyData.value.map(d => d.date),
            axisLine: { lineStyle: { color: '#334155' } },
            axisLabel: { color: '#64748b', fontSize: 9 }
        },
        yAxis: {
            type: 'value',
            scale: true,
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
            axisLabel: { color: '#64748b', fontSize: 9, formatter: (v) => v.toFixed(2) }
        },
        series: [{
            name: `${selectedTerm.value} ${props.activeTab}`,
            data: historyData.value.map(d => d.yield),
            type: 'line',
            smooth: true,
            showSymbol: false,
            itemStyle: { color: '#38bdf8' },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(56, 189, 248, 0.2)' },
                    { offset: 1, color: 'rgba(56, 189, 248, 0)' }
                ])
            }
        }]
    })
}

const initCharts = async () => {
  await nextTick()
  if (chartEl.value) {
    if (!chart.value) chart.value = echarts.init(chartEl.value)
    fetchMultiCurve()
  }
  if (trendChartEl.value) {
    if (!trendChart.value) trendChart.value = echarts.init(trendChartEl.value)
    selectedTerm.value = '10Y' // Ensure default
    fetchHistory()
  }
}

watch(() => props.activeTab, () => {
  fetchMultiCurve()
  fetchHistory()
})

watch(selectedTerm, () => {
    fetchHistory()
})

watch(() => props.allCurves, () => {
  fetchMultiCurve()
}, { deep: true })

onMounted(() => {
  initCharts()
  window.addEventListener('resize', () => {
    chart.value?.resize()
    trendChart.value?.resize()
  })
})
</script>

<template>
  <div class="space-y-4">
    
    <!-- TOP TABS -->
    <section class="grid grid-cols-5 gap-3">
      <button 
        v-for="type in bondTypes" 
        :key="type"
        @click="$emit('update:activeTab', type)"
        :class="[
          'relative p-3 rounded-xl border text-left transition-all group overflow-hidden',
          activeTab === type 
            ? 'bg-sky-500/10 border-sky-500/40 shadow-[0_0_15px_rgba(14,165,233,0.15)]' 
            : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
        ]"
      >
        <div v-if="activeTab === type" class="absolute top-0 left-0 w-full h-0.5 bg-sky-500"></div>
        <div class="flex flex-col gap-0.5">
          <div class="flex items-center gap-1.5 text-[10px] font-black tracking-tight text-slate-500 uppercase">
            <span class="text-sky-500">10Y</span> {{ type }}
            <span class="text-[9px] font-medium text-slate-600 opacity-60">({{ selectedDate?.slice(5) }})</span>
          </div>
          <div class="flex items-baseline justify-between mt-1">
            <div class="flex items-baseline gap-1">
              <span class="text-xl font-black text-white tracking-tighter">{{ getTopYield(type) }}</span>
              <span class="text-[10px] font-bold text-slate-500 opacity-50">%</span>
            </div>
            <div :class="['text-[11px] font-bold font-mono mb-1', getChangeColor(getTopChange(type))]">
              {{ parseFloat(getTopChange(type)) > 0 ? '+' : '' }}{{ getTopChange(type) }}BP
            </div>
          </div>
        </div>
      </button>
    </section>

    <!-- CONTENT -->
    <div class="space-y-6">
        <section class="space-y-4">
            <div class="flex items-center justify-between px-1">
                <div class="flex items-center gap-2">
                    <div class="w-1.5 h-3.5 bg-sky-500 rounded-full shadow-[0_0_8px_#0ea5e9]"></div>
                    <span class="text-[11px] font-black text-white uppercase tracking-widest">{{ activeTab }} 收益率曲线追踪</span>
                </div>
                <div class="text-[10px] text-slate-500 font-bold bg-sky-500/5 px-2 py-0.5 rounded border border-sky-500/10 uppercase tracking-widest">REAL-TIME VALUATION</div>
            </div>

            <div class="grid grid-cols-12 gap-6">
                <!-- Data Table -->
                <div class="col-span-12 xl:col-span-6 bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-inner flex flex-col h-[724px]">
                    <!-- Table Header -->
                    <div class="bg-slate-900 border-b border-slate-800 flex items-center h-10 px-4">
                        <div class="w-16 font-black text-slate-500 uppercase tracking-tighter text-[9px]">期限</div>
                        <div class="w-20 font-black text-slate-500 uppercase tracking-tighter text-[9px]">昨收 ({{ prevDate?.slice(5) }})</div>
                        <div class="w-20 font-black text-slate-500 uppercase tracking-tighter text-[9px]">最新 ({{ selectedDate?.slice(5) }})</div>
                        <div class="w-24 font-black text-slate-500 uppercase tracking-tighter text-[9px]">日变动 (BP)</div>
                        <div class="flex-1 font-black text-slate-500 uppercase tracking-tighter text-[9px]">分位 (1Y)</div>
                    </div>
                    <!-- Table Body (Adaptive Rows) -->
                    <div class="flex-1 flex flex-col divide-y divide-slate-800/40">
                        <div 
                            v-for="row in allCurves[activeTab]" 
                            :key="row.term" 
                            @click="selectedTerm = row.term"
                            :class="[
                                'flex-1 flex items-center px-4 hover:bg-sky-500/5 transition-all group cursor-pointer',
                                selectedTerm === row.term ? 'bg-sky-500/10 border-l-2 border-sky-500' : ''
                            ]"
                        >
                            <div class="w-16 font-bold text-slate-400 group-hover:text-white transition-colors text-[11px]">{{ row.term }}</div>
                            <div class="w-20 font-mono text-slate-500 italic text-[11px]">{{ format4(parseFloat(row.yield) - parseFloat(row.change)/100) }}</div>
                            <div class="w-20 font-mono font-bold text-sky-400 group-hover:text-sky-300 text-[11px]">{{ format4(row.yield) }}</div>
                            <div :class="['w-24 font-mono font-bold text-[11px]', getChangeColor(row.change)]">
                                {{ parseFloat(row.change) > 0 ? '+' : '' }}{{ format4(row.change) }}
                            </div>
                            <div class="flex-1">
                                <div class="flex items-center gap-3">
                                    <div class="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                                        <div class="h-full bg-sky-500/40 group-hover:bg-sky-500/60 transition-all" :style="{ width: (row.percentile * 100) + '%' }"></div>
                                    </div>
                                    <span class="text-[9px] font-mono text-slate-500 group-hover:text-slate-400">{{ (row.percentile * 100).toFixed(1) }}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Visualization -->
                <div class="col-span-12 xl:col-span-6 flex flex-col gap-6">
                    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 flex flex-col h-[350px] shadow-2xl relative group">
                        <div class="absolute top-6 right-6 flex items-center gap-2">
                            <div class="w-2 h-2 rounded-full bg-sky-500 animate-pulse"></div>
                            <span class="text-[9px] font-black text-sky-500/60 uppercase tracking-widest">LIVE STREAM</span>
                        </div>
                        <div class="text-[10px] font-black text-slate-500 uppercase mb-4 tracking-widest">{{ activeTab }} 期限结构 (Yield Curve)</div>
                        <div ref="chartEl" class="flex-1 w-full"></div>
                    </div>

                    <!-- Trend Chart Widget -->
                    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 flex flex-col h-[350px] shadow-2xl relative group">
                        <div class="flex items-center justify-between mb-4">
                             <div class="text-[10px] font-black text-slate-500 uppercase tracking-widest">{{ selectedTerm }} {{ activeTab }} 历史走势</div>
                             <div class="text-[9px] font-bold text-sky-400 bg-sky-400/10 px-2 py-0.5 rounded">HISTORICAL TREND</div>
                        </div>
                        <div ref="trendChartEl" class="flex-1 w-full"></div>
                    </div>
                </div>
            </div>

            <!-- Market Context Widget -->
            <div class="bg-gradient-to-br from-sky-500/10 to-transparent border border-sky-500/20 rounded-3xl p-6 flex flex-col gap-4 mt-6">
                <h4 class="text-[11px] font-black text-white uppercase tracking-widest">市场简评 (AI Insight)</h4>
                <p class="text-[12px] text-slate-400 leading-relaxed italic">
                    当前 {{ activeTab }} 曲线呈现 {{ parseFloat(allCurves[activeTab][15]?.yield) > parseFloat(allCurves[activeTab][6]?.yield) ? '陡峭化' : '平坦化' }} 趋势。
                    10Y 收益率处于近一年 {{ (allCurves[activeTab][15]?.percentile * 100).toFixed(1) }}% 分位，具备一定的{{ allCurves[activeTab][15]?.percentile > 0.5 ? '配置' : '交易' }}价值。
                </p>
            </div>
        </section>
    </div>
  </div>
</template>

<style scoped>
.shadow-inner { box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06); }
table { height: auto; }
</style>
