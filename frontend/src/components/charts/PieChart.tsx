/**
 * Pie Chart Component
 * Displays distribution data
 */
import { PieChart as RechartsPieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface PieChartProps {
  data: Array<{
    name: string
    value: number
  }>
  colors?: string[]
  height?: number
}

const DEFAULT_COLORS = [
  '#4f46e5', // indigo-600
  '#10b981', // emerald-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#8b5cf6', // violet-500
  '#ec4899', // pink-500
  '#06b6d4', // cyan-500
]

export function PieChart({ data, colors = DEFAULT_COLORS, height = 300 }: PieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={(props: {name?: string; percent?: number}) => {
            const name = props.name || ''
            const percent = props.percent || 0
            return `${name} ${(percent * 100).toFixed(0)}%`
          }}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip 
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
          }}
        />
        <Legend 
          wrapperStyle={{ fontSize: '12px' }}
          verticalAlign="bottom"
        />
      </RechartsPieChart>
    </ResponsiveContainer>
  )
}

