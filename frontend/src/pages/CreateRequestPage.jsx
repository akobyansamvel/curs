import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import MapPicker from '../components/map/MapPicker'
import Breadcrumbs from '../components/common/Breadcrumbs'
import { getMediaUrl } from '../services/mediaUrl'
import './CreateRequestPage.css'

function CreateRequestPage() {
  const [formData, setFormData] = useState({
    request_type: 'sport',
    activity_id: '',
    format: 'partner',
    date: '',
    time: '',
    date_end: '',
    time_end: '',
    location_name: '',
    latitude: '',
    longitude: '',
    address: '',
    level: 'any',
    max_participants: 2,
    title: '',
    description: '',
    requirements: '',
    visibility: 'public',
    rules_accepted: false
  })
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [photos, setPhotos] = useState([])
  const [uploadingPhotos, setUploadingPhotos] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadActivities()
  }, [formData.request_type])

  const loadActivities = async () => {
    try {
      const response = await api.get('/requests/activities/', {
        params: {
          category_id: formData.request_type === 'sport' ? 1 : 2
        }
      })
      setActivities(response.data)
    } catch (error) {
      console.error('Ошибка загрузки активностей:', error)
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    })
  }

  const handleMapSelect = (location) => {
    if (!location || (location.latitude == null && location.longitude == null)) {
      setFormData({
        ...formData,
        location_name: '',
        latitude: '',
        longitude: '',
        address: ''
      })
      return
    }

    setFormData({
      ...formData,
      location_name: location.name,
      latitude: location.latitude,
      longitude: location.longitude,
      address: location.address
    })
  }

  const handlePhotoUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    setUploadingPhotos(true)
    try {
      const uploadedUrls = []
      for (const file of files) {
        const formData = new FormData()
        formData.append('photo', file)
        
        const response = await api.post('/requests/upload-photo/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        uploadedUrls.push(response.data.url)
      }
      setPhotos([...photos, ...uploadedUrls])
    } catch (error) {
      console.error('Ошибка загрузки фото:', error)
      alert('Не удалось загрузить фото')
    } finally {
      setUploadingPhotos(false)
    }
  }

  const handleRemovePhoto = (index) => {
    setPhotos(photos.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.rules_accepted) {
      setError('Необходимо согласиться с правилами')
      return
    }

    setLoading(true)
    setError('')

    try {
      const roundCoordinate = (coord) => {
        if (coord === null || coord === undefined || coord === '') return null
        const num = typeof coord === 'string' ? parseFloat(coord) : coord
        if (isNaN(num)) return null
        return parseFloat(num.toFixed(6))
      }
      
      const submitData = {
        ...formData,
        photos: photos,
        latitude: roundCoordinate(formData.latitude),
        longitude: roundCoordinate(formData.longitude)
      }
      await api.post('/requests/create/', submitData)
      navigate('/requests/my')
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка создания заявки')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="create-request-page">
      <Breadcrumbs
        items={[
          { label: 'Главная', to: '/' },
          { label: 'Создание заявки' }
        ]}
      />
      <h1>Создать заявку</h1>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit} className="request-form">
        <div className="form-group">
          <label>Тип</label>
          <select name="request_type" value={formData.request_type} onChange={handleChange} required>
            <option value="sport">Спорт</option>
            <option value="entertainment">Развлечения</option>
          </select>
        </div>

        <div className="form-group">
          <label>Активность</label>
          <select name="activity_id" value={formData.activity_id} onChange={handleChange} required>
            <option value="">Выберите активность</option>
            {activities.map(activity => (
              <option key={activity.id} value={activity.id}>{activity.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Формат</label>
          <select name="format" value={formData.format} onChange={handleChange} required>
            <option value="partner">Партнёр</option>
            <option value="company">Компания</option>
            <option value="group">Группа</option>
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Дата</label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label>Время</label>
            <input
              type="time"
              name="time"
              value={formData.time}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label>Место</label>
          <input
            id="location_name_input"
            type="text"
            name="location_name"
            value={formData.location_name}
            onChange={handleChange}
            placeholder="Начните вводить адрес или место"
            required
          />
          <MapPicker
            onSelect={handleMapSelect}
            address={formData.location_name}
            addressInputId="location_name_input"
          />
          {formData.address && (
            <p className="address">{formData.address}</p>
          )}
        </div>

        <div className="form-group">
          <label>Уровень</label>
          <select name="level" value={formData.level} onChange={handleChange}>
            <option value="any">Любой</option>
            <option value="beginner">Начинающий</option>
            <option value="intermediate">Средний</option>
            <option value="advanced">Продвинутый</option>
            <option value="professional">Профессионал</option>
          </select>
        </div>

        <div className="form-group">
          <label>Количество участников</label>
          <input
            type="number"
            name="max_participants"
            value={formData.max_participants}
            onChange={handleChange}
            min="1"
            required
          />
        </div>

        <div className="form-group">
          <label>Заголовок</label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Краткое описание заявки"
            required
          />
        </div>

        <div className="form-group">
          <label>Описание</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="5"
            placeholder="Подробное описание активности"
            required
          />
        </div>

        <div className="form-group">
          <label>Требования</label>
          <textarea
            name="requirements"
            value={formData.requirements}
            onChange={handleChange}
            rows="3"
            placeholder="Например: только с инвентарём"
          />
        </div>

        <div className="form-group">
          <label>Фото (необязательно)</label>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handlePhotoUpload}
            disabled={uploadingPhotos}
          />
          {uploadingPhotos && <p>Загрузка фото...</p>}
          {photos.length > 0 && (
            <div className="photos-preview">
              {photos.map((url, index) => (
                <div key={index} className="photo-preview">
                  <img src={getMediaUrl(url)} alt={`Фото ${index + 1}`} />
                  <button
                    type="button"
                    onClick={() => handleRemovePhoto(index)}
                    className="remove-photo"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="form-group">
          <label>Видимость</label>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                name="visibility"
                value="public"
                checked={formData.visibility === 'public'}
                onChange={handleChange}
              />
              Публичная
            </label>
            <label>
              <input
                type="radio"
                name="visibility"
                value="link"
                checked={formData.visibility === 'link'}
                onChange={handleChange}
              />
              Только по ссылке
            </label>
          </div>
        </div>

        <div className="form-group form-group-checkbox">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="rules_accepted"
              checked={formData.rules_accepted}
              onChange={handleChange}
              required
            />
            <span>Согласен с правилами</span>
          </label>
        </div>

        <button type="submit" disabled={loading} className="submit-button">
          {loading ? 'Создание...' : 'Создать заявку'}
        </button>
      </form>
    </div>
  )
}

export default CreateRequestPage
