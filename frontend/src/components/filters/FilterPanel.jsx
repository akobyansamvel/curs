import { useState, useEffect } from 'react'
import api from '../../services/api'
import './FilterPanel.css'

function FilterPanel({ filters, onChange }) {
  const [categories, setCategories] = useState([])
  const [activities, setActivities] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [catsRes, actsRes] = await Promise.all([
        api.get('/requests/categories/'),
        api.get('/requests/activities/')
      ])
      setCategories(catsRes.data)
      setActivities(actsRes.data)
    } catch (error) {
      console.error('Ошибка загрузки данных:', error)
    }
  }

  const handleChange = (name, value) => {
    onChange({
      ...filters,
      [name]: value
    })
  }

  return (
    <div className="filter-panel">
      <input
        type="text"
        placeholder="Поиск..."
        value={filters.q}
        onChange={(e) => handleChange('q', e.target.value)}
        className="search-input"
      />
      
      <select
        value={filters.category_id}
        onChange={(e) => handleChange('category_id', e.target.value)}
      >
        <option value="">Все категории</option>
        {categories.map(cat => (
          <option key={cat.id} value={cat.id}>{cat.name}</option>
        ))}
      </select>

      <select
        value={filters.activity_id}
        onChange={(e) => handleChange('activity_id', e.target.value)}
      >
        <option value="">Все активности</option>
        {activities.map(act => (
          <option key={act.id} value={act.id}>{act.name}</option>
        ))}
      </select>

      <select
        value={filters.level}
        onChange={(e) => handleChange('level', e.target.value)}
      >
        <option value="">Любой уровень</option>
        <option value="beginner">Начинающий</option>
        <option value="intermediate">Средний</option>
        <option value="advanced">Продвинутый</option>
        <option value="professional">Профессионал</option>
      </select>
    </div>
  )
}

export default FilterPanel
