<script setup>
import { ref, onMounted, watch, shallowRef, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  allCurves: Object,
  selectedDate: String,
  prevDate: String
})

const activeContract = ref('T2406')
const contracts = [
  { id: 'TS2406', name: '2Y 国债期货', price: 101.250, change: 0.055, basis: 0.12, yield: 2.15 },
  { id: 'TF2406', name: '5Y 国债期货', price: 102.840, change: 0.120, basis: 0.15, yield: 2.32 },
  { id: 'T2406', name: '10Y 国债期货', price: 104.150, change: 0.185, basis: 0.22, yield: 2.45 },
  { id: 'TL2406', name: '30Y 国债期货', price: 107.500, change: 0.420, basis: 0.35, yield: 2.68 }
]

const ctdBonds = ref([
  { code: '230025.IB', name: '23 附息国债 25', term: '10.0Y', cf: 0.9852, price: 102.85, yield: 2.44, basis: 0.21, bnoc: 0.05, irr: 2.15, isCtd: true },
  { code: '240004.IB', name: '24 附息国债 04', term: '9.8Y', cf: 0.9745, price: 101.75, yield: 2.46, basis: 0.25, bnoc: 0.08, irr: 1.95, isCtd: false },
  { code: '230018.IB', name: '23 附息国债 18', term: '9.5Y', cf: 0.9650, price: 100.90, yield: 2.48, basis: 0.28, bnoc: 0.12, irr: 1.80, isCtd: false }
])

const curveChartEl = ref(null)
const basisTrendChartEl = ref(null)
const curveChart = shallowRef(null)
const basisTrendChart = shallowRef(null)

const format4 = (val) => parseFloat(val).toFixed(4)
const getChangeColor = (val) => {
  const num = parseFloat(val)
  if (num > 0) return 'text-rose-500'
  if (num < 0) return 'text-emerald-500'
  return 'text-slate-500'
}

const updateCharts = () => {
  if (!curveChart.value || !basisTrendChart.value) return

  // Implied Yield Curve Chart
  const treasuryPoints = (props.allCurves['国债'] || [])
    .filter(p => ['2Y', '5Y', '10Y', '30Y'].includes(p.term))
    .map(p => [parseFloat(p.term), p.yield])
    .sort((a,b) => a[0]-b[0])

  const impliedPoints = contracts.map(c => {
    const term = parseInt(c.id.slice(0, 2) === 'TS' ? 2 : (c.id.slice(0, 2) === 'TF' ? 5 : (c.id.slice(0, 2) === 'T' ? 10 : 30)))
    return [term, c.yield]
  }).sort((a,b) => a[0]-b[0])

  const curveOption = {
    backgroundColor: 'transparent',
    legend: { show: true, bottom: 0, textStyle: { color: '#64748b', fontSize: 10 } },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.9)', textStyle: { color: '#f1f5f9' } },
    grid: { top: 40, bottom: 60, left: 50, right: 30 },
    xAxis: { type: 'value', min: 0, max: 35, axisLabel: { color: '#64748b', formatter: '{value}Y' }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.1)' } } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: '#64748b', formatter: '{value}%' }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.1)' } } },
    series: [
      { name: '中债国债收益率', data: treasuryPoints, type: 'line', smooth: true, itemStyle: { color: '#f59e0b' }, lineStyle: { width: 2 } },
      { name: '期货合成收益率', data: impliedPoints, type: 'line', smooth: true, itemStyle: { color: '#0ea5e9' }, lineStyle: { width: 2, type: 'dashed' } }
    ]
  }
  curveChart.value.setOption(curveOption)

  // Basis Trend Chart
  const basisTrendOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.9)' },
    grid: { top: 40, bottom: 40, left: 50, right: 30 },
    xAxis: { type: 'category', data: ['05-01', '05-02', '05-03', '05-04', '05-05', '05-06', '05-07', '05-08', '05-09', '05-10'], axisLabel: { color: '#64748b' } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.1)' } } },
    series: [{ 
      name: 'Basis', 
      data: [0.18, 0.20, 0.19, 0.22, 0.25, 0.23, 0.21, 0.24, 0.22, 0.21], 
      type: 'line', smooth: true, showSymbol: false,
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(245, 158, 11, 0.2)' }, { offset: 1, color: 'rgba(245, 158, 11, 0)' }]) },
      itemStyle: { color: '#f59e0b' }
    }]
  }
  basisTrendChart.value.setOption(basisTrendOption)
}

onMounted(async () => {
  await nextTick()
  if (curveChartEl.value) curveChart.value = echarts.init(curveChartEl.value)
  if (basisTrendChartEl.value) basisTrendChart.value = echarts.init(basisTrendChartEl.value)
  updateCharts()
  window.addEventListener('resize', () => {
    curveChart.value?.resize()
    basisTrendChart.value?.resize()
  })
})

watch(() => [props.allCurves, activeContract.value], () => updateCharts(), { deep: true })
</script>

<template>
  <div class="space-y-4">
    <!-- Futures Contract Tickers -->
    <div class="grid grid-cols-4 gap-3">
      <button 
        v-for="c in contracts" 
        :key="c.id"
        @click="activeContract = c.id"
        :class="[
          'relative p-3 rounded-2xl border text-left transition-all group overflow-hidden',
          activeContract === c.id 
            ? 'bg-sky-500/10 border-sky-500/40 shadow-[0_0_20px_rgba(14,165,233,0.15)]' 
            : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
        ]"
      >
        <div v-if="activeContract === c.id" class="absolute top-0 left-0 w-full h-1 bg-sky-500"></div>
        <div class="flex flex-col gap-1">
          <div class="flex items-center justify-between text-[10px] font-black tracking-widest uppercase">
            <span class="text-slate-500">{{ c.name }}</span>
            <span class="text-sky-500">{{ c.id }}</span>
          </div>
          <div class="flex items-baseline justify-between mt-1">
            <span class="text-xl font-black text-white tracking-tighter">{{ c.price.toFixed(3) }}</span>
            <div :class="['text-[10px] font-bold font-mono px-1.5 py-0.5 rounded bg-slate-950/50', getChangeColor(c.change)]">
              {{ c.change > 0 ? '+' : '' }}{{ c.change.toFixed(3) }}
            </div>
          </div>
          <div class="flex items-center justify-between mt-1 text-[9px] font-bold uppercase tracking-tight">
             <span class="text-slate-600">Basis</span>
             <span class="text-amber-500 font-mono">{{ c.basis.toFixed(2) }}</span>
          </div>
        </div>
      </button>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-12 gap-3">
      <!-- Left Column: CTD Analysis -->
      <div class="col-span-12 xl:col-span-7 space-y-3">
        <div class="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-inner flex flex-col h-[653px]">
          <div class="bg-slate-900 border-b border-slate-800 flex items-center h-8 px-4 justify-between">
            <div class="flex items-center gap-2">
              <div class="w-1.5 h-3.5 bg-sky-500 rounded-full"></div>
              <span class="text-[10px] font-black text-white uppercase tracking-widest">{{ activeContract }} 可交割券分析 (CTD Basket)</span>
            </div>
            <div class="text-[9px] text-slate-500 font-bold uppercase tracking-widest">Pricing & Arbitrage Metrics</div>
          </div>
          
          <div class="flex-1 overflow-auto custom-scrollbar">
            <table class="w-full text-left border-collapse">
              <thead class="bg-slate-900/50 sticky top-0 z-10">
                <tr>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter">债券代码</th>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter">简称</th>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter">CF</th>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter text-right">现货价格</th>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter text-right">收益率</th>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter text-right">基差</th>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter text-right">BNOC</th>
                  <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase tracking-tighter text-right">IRR (%)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/40">
                <tr v-for="bond in ctdBonds" :key="bond.code" :class="['hover:bg-sky-500/5 transition-colors group cursor-pointer', bond.isCtd ? 'bg-amber-500/5' : '']">
                  <td class="px-4 py-2 font-mono text-[11px] flex items-center gap-2">
                    <span :class="bond.isCtd ? 'text-amber-500' : 'text-slate-400'">{{ bond.code }}</span>
                    <span v-if="bond.isCtd" class="text-[8px] bg-amber-500/20 text-amber-500 px-1 rounded font-black">CTD</span>
                  </td>
                  <td class="px-4 py-2 text-[11px] font-bold text-slate-300">{{ bond.name }}</td>
                  <td class="px-4 py-2 text-[11px] font-mono text-slate-500">{{ bond.cf.toFixed(4) }}</td>
                  <td class="px-4 py-2 text-[11px] font-mono text-slate-200 text-right">{{ bond.price.toFixed(2) }}</td>
                  <td class="px-4 py-2 text-[11px] font-mono text-slate-400 text-right">{{ bond.yield.toFixed(4) }}%</td>
                  <td class="px-4 py-2 text-[11px] font-mono font-bold text-amber-500 text-right">{{ bond.basis.toFixed(4) }}</td>
                  <td class="px-4 py-2 text-[11px] font-mono text-slate-400 text-right">{{ bond.bnoc.toFixed(4) }}</td>
                  <td class="px-4 py-2 text-[11px] font-mono font-bold text-sky-400 text-right">{{ bond.irr.toFixed(2) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- Bottom Info -->
          <div class="p-4 bg-slate-950/40 border-t border-slate-800 grid grid-cols-3 gap-4">
             <div class="space-y-1">
                <div class="text-[9px] font-black text-slate-600 uppercase">Selected CTD</div>
                <div class="text-sm font-black text-amber-500">230025.IB</div>
             </div>
             <div class="space-y-1">
                <div class="text-[9px] font-black text-slate-600 uppercase">Implied Yield</div>
                <div class="text-sm font-black text-white">2.4485%</div>
             </div>
             <div class="space-y-1">
                <div class="text-[9px] font-black text-slate-600 uppercase">Basis Convergence</div>
                <div class="text-sm font-black text-sky-500">Converging</div>
             </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Charts -->
      <div class="col-span-12 xl:col-span-5 space-y-3">
        <!-- Implied Yield Curve -->
        <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-4 flex flex-col h-[320px] shadow-2xl relative group">
          <div class="flex items-center justify-between mb-2">
            <div class="text-[10px] font-black text-slate-500 uppercase tracking-widest">期货合成收益率曲线</div>
            <div class="text-[8px] bg-sky-500/10 text-sky-500 px-2 py-0.5 rounded font-black tracking-widest uppercase">Yield Curve Comparison</div>
          </div>
          <div ref="curveChartEl" class="flex-1 w-full"></div>
        </div>

        <!-- Basis Trend -->
        <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-4 flex flex-col h-[320px] shadow-2xl relative group">
          <div class="flex items-center justify-between mb-2">
            <div class="text-[10px] font-black text-slate-500 uppercase tracking-widest">{{ activeContract }} 基差走势</div>
            <div class="text-[8px] bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded font-black tracking-widest uppercase">Historical Basis</div>
          </div>
          <div ref="basisTrendChartEl" class="flex-1 w-full"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
</style>
