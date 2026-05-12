<script setup>
const props = defineProps({
  data: Array,
  title: String
})

const format4 = (val) => parseFloat(val).toFixed(4)
const getChangeColor = (val) => {
  const num = parseFloat(val)
  if (num > 0) return 'text-rose-500'
  if (num < 0) return 'text-emerald-500'
  return 'text-slate-500'
}
</script>

<template>
  <div class="grid grid-cols-1 gap-6">
    <div class="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      <table class="w-full text-left border-collapse text-[11px]">
        <thead class="bg-slate-900 border-b border-slate-800">
          <tr>
            <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase">项目</th>
            <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase">昨收</th>
            <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase">今收</th>
            <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase">变动</th>
            <th class="px-4 py-2 text-[9px] font-black text-slate-500 uppercase">分位</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/30">
          <tr v-for="row in data" :key="row.name" class="hover:bg-slate-800 transition-colors">
            <td class="px-4 py-1.5 font-bold text-slate-300">{{ row.name }}</td>
            <td class="px-4 py-1.5 font-mono text-slate-500 italic">{{ format4(parseFloat(row.value) - parseFloat(row.change)/100) }}</td>
            <td class="px-4 py-1.5 font-mono text-slate-200">{{ format4(row.value) }}</td>
            <td :class="['px-4 py-1.5 font-mono', getChangeColor(row.change)]">{{ format4(row.change) }}</td>
            <td class="px-4 py-1.5">
               <div class="flex items-center gap-3">
                 <div class="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                   <div class="h-full bg-sky-500/20" :style="{ width: (row.percentile * 100) + '%' }"></div>
                 </div>
                 <span class="text-[9px] font-mono text-slate-500">{{ (row.percentile * 100).toFixed(1) }}%</span>
               </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
