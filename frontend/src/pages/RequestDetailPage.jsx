import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import ParticipantsList from '../components/requests/ParticipantsList'
import CreateReview from '../components/reviews/CreateReview'
import EditRequestForm from '../components/requests/EditRequestForm'
import CreateComplaint from '../components/complaints/CreateComplaint'
import DeleteRequestModal from '../components/requests/DeleteRequestModal'
import Breadcrumbs from '../components/common/Breadcrumbs'
import MapPicker from '../components/map/MapPicker'
import { getMediaUrl } from '../services/mediaUrl'
import './RequestDetailPage.css'

function RequestDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [request, setRequest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [participating, setParticipating] = useState(false)
  const [favorited, setFavorited] = useState(false)
  const [message, setMessage] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [showChangeLocationModal, setShowChangeLocationModal] = useState(false)
  const [newLocation, setNewLocation] = useState({ location_name: '', latitude: '', longitude: '', address: '' })
  const [creatingChat, setCreatingChat] = useState(false)
  const [showComplaint, setShowComplaint] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [photoIndex, setPhotoIndex] = useState(0)
  
  const isModerator = user?.is_moderator || user?.is_staff
  const photos = request?.photos && request.photos.length > 0 ? request.photos : []
  const hasMultiplePhotos = photos.length > 1

  useEffect(() => {
    loadRequest()
  }, [id])

  useEffect(() => {
    setPhotoIndex(0)
  }, [id])

  const loadRequest = async () => {
    try {
      const [requestRes, participationsRes] = await Promise.all([
        api.get(`/requests/${id}/`),
        user ? api.get(`/requests/${id}/participations/`).catch(() => ({ data: [] })) : Promise.resolve({ data: [] })
      ])
      
      const requestData = { ...requestRes.data }
      if (participationsRes.data) {
        requestData.participations = participationsRes.data
      }
      setRequest(requestData)
      
      if (user) {
        if (requestRes.data.is_favorite !== undefined) {
          setFavorited(requestRes.data.is_favorite)
        } else {
          try {
            const favoriteRes = await api.get(`/requests/${id}/favorite/`)
            setFavorited(favoriteRes.data.is_favorite || false)
          } catch (error) {
            setFavorited(false)
          }
        }
      } else {
        setFavorited(false)
      }
      
      if (user) {
        if (requestRes.data.is_participating !== undefined) {
          setParticipating(requestRes.data.is_participating)
        } else if (requestRes.data.participations) {
          const userParticipation = requestRes.data.participations.find(
            p => p.user?.id === user.id && p.status === 'approved'
          )
          setParticipating(!!userParticipation)
        } else {
          try {
            const participationRes = await api.get(`/requests/${id}/participations/`).catch(() => ({ data: [] }))
            const userParticipation = participationRes.data?.find(
              p => p.user?.id === user.id && p.status === 'approved'
            )
            setParticipating(!!userParticipation)
          } catch (error) {
            setParticipating(false)
          }
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки заявки:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleParticipate = async () => {
    if (!user) {
      navigate('/login')
      return
    }

    try {
      await api.post(`/requests/${id}/participate/`, { message })
      setParticipating(true)
      setMessage('')
      loadRequest()
    } catch (error) {
      console.error('Ошибка отклика:', error)
    }
  }

  const handleToggleFavorite = async () => {
    if (!user) {
      navigate('/login')
      return
    }

    try {
      if (favorited) {
        const response = await api.delete(`/requests/${id}/favorite/`)
        setFavorited(response.data?.is_favorite || false)
      } else {
        const response = await api.post(`/requests/${id}/favorite/`)
        setFavorited(response.data?.is_favorite || true)
      }
    } catch (error) {
      console.error('Ошибка избранного:', error)
      alert('Не удалось изменить статус избранного')
    }
  }

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
  }

  const handleSaveEdit = (updatedRequest) => {
    setRequest(updatedRequest)
    setIsEditing(false)
    loadRequest()
  }

  const handleCancelRequest = async () => {
    if (!window.confirm('Вы уверены, что хотите отменить эту заявку? Все участники будут уведомлены.')) {
      return
    }

    try {
      await api.patch(`/requests/${id}/edit/`, { status: 'cancelled' })
      loadRequest()
      setShowCancelModal(false)
    } catch (error) {
      console.error('Ошибка отмены заявки:', error)
      alert('Не удалось отменить заявку')
    }
  }

  const handleChangeLocation = async () => {
    if (!newLocation.location_name) {
      alert('Укажите место')
      return
    }

    try {
      const roundCoordinate = (coord) => {
        if (coord === null || coord === undefined || coord === '') return null
        const num = typeof coord === 'string' ? parseFloat(coord) : coord
        if (isNaN(num)) return null
        return parseFloat(num.toFixed(6))
      }

      await api.patch(`/requests/${id}/edit/`, {
        location_name: newLocation.location_name,
        latitude: roundCoordinate(newLocation.latitude),
        longitude: roundCoordinate(newLocation.longitude),
        address: newLocation.address || ''
      })
      loadRequest()
      setShowChangeLocationModal(false)
      setNewLocation({ location_name: '', latitude: '', longitude: '', address: '' })
    } catch (error) {
      console.error('Ошибка изменения места:', error)
      alert('Не удалось изменить место')
    }
  }

  if (loading) {
    return <div className="request-detail-page">Загрузка...</div>
  }

  if (!request) {
    return <div className="request-detail-page">Заявка не найдена</div>
  }

  const isCreator = user && user.id === request.creator?.id

  const handleDeleteRequest = async (comment) => {
    try {
      await api.delete(`/requests/${id}/delete/`, {
        data: { reason: comment }
      })
      setShowDeleteModal(false)
      navigate('/')
      alert('Заявка удалена')
    } catch (error) {
      console.error('Ошибка удаления заявки:', error)
      alert('Не удалось удалить заявку')
      throw error
    }
  }

  const handleStartGroupChat = async () => {
    if (!user) {
      navigate('/login')
      return
    }

    if (!participating && !isCreator) {
      alert('Вы должны участвовать в активности, чтобы открыть чат')
      return
    }

      setCreatingChat(true)
    try {
      const response = await api.post(`/chat/create-request/${id}/`)
      navigate(`/chat/${response.data.id}`)
    } catch (error) {
      console.error('Ошибка создания чата:', error)
      alert(error.response?.data?.error || 'Не удалось создать чат')
    } finally {
      setCreatingChat(false)
    }
  }

  const totalParticipants = 1 + (request.current_participants || 0)
  const canShowGroupChat = (participating || isCreator) && 
                           totalParticipants >= 3

  return (
    <div className="request-detail-page">
      <Breadcrumbs
        items={[
          { label: 'Главная', to: '/' },
          { label: request.title || 'Заявка' }
        ]}
      />
      <div className="request-header">
        <h1>{request.title}</h1>
        <div className="request-header-actions">
          {user && !isCreator && (
            <>
              <button
                onClick={handleToggleFavorite}
                className={`favorite-button ${favorited ? 'active' : ''}`}
              >
                {favorited ? '★' : '☆'}
              </button>
              <button
                onClick={() => setShowComplaint(!showComplaint)}
                className="complaint-button"
                title="Пожаловаться на заявку"
              >
                ⚠️ Пожаловаться
              </button>
            </>
          )}
        </div>
      </div>

      {user && !isCreator && showComplaint && (
        <CreateComplaint
          reportedRequest={request}
          onSuccess={() => setShowComplaint(false)}
          onCancel={() => setShowComplaint(false)}
        />
      )}

      <div className="request-main-row">
        <div className="request-photos-col">
          {photos.length > 0 ? (
            <div className="request-photo-carousel">
              <div className="carousel-inner">
                <img
                  src={getMediaUrl(photos[photoIndex])}
                  alt={`Фото ${photoIndex + 1}`}
                  className="request-photo"
                />
              </div>
              {hasMultiplePhotos && (
                <>
                  <button
                    type="button"
                    className="carousel-btn carousel-prev"
                    onClick={() => setPhotoIndex((i) => (i === 0 ? photos.length - 1 : i - 1))}
                    aria-label="Предыдущее фото"
                  >
                    ‹
                  </button>
                  <button
                    type="button"
                    className="carousel-btn carousel-next"
                    onClick={() => setPhotoIndex((i) => (i === photos.length - 1 ? 0 : i + 1))}
                    aria-label="Следующее фото"
                  >
                    ›
                  </button>
                  <div className="carousel-dots">
                    {photos.map((_, i) => (
                      <button
                        key={i}
                        type="button"
                        className={`carousel-dot ${i === photoIndex ? 'active' : ''}`}
                        onClick={() => setPhotoIndex(i)}
                        aria-label={`Фото ${i + 1}`}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="request-photo-placeholder">
              <span>Нет фото</span>
            </div>
          )}
          <div className="request-creator">
            <h3 className="request-creator-title">Создатель</h3>
            {request.creator ? (
              <Link to={`/profile/${request.creator.id}/`} className="creator-link">
                {request.creator.username}
              </Link>
            ) : (
              <span>Не указан</span>
            )}
          </div>
        </div>

        <div className="request-data-col">
          <div className="request-data-block">
            <div className="request-info">
              <div className="info-item">
                <strong>Активность:</strong> {request.activity?.name}
              </div>
              <div className="info-item">
                <strong>Формат:</strong> {request.format === 'partner' ? 'Партнёр' : 
                                          request.format === 'company' ? 'Компания' : 'Группа'}
              </div>
              <div className="info-item">
                <strong>Дата и время:</strong> {new Date(request.date).toLocaleDateString('ru-RU')} в {request.time}
              </div>
              <div className="info-item">
                <strong>Место:</strong> {request.address || request.location_name}
              </div>
              <div className="info-item">
                <strong>Уровень:</strong> {
                  request.level === 'beginner' ? 'Начинающий' :
                  request.level === 'intermediate' ? 'Средний' :
                  request.level === 'advanced' ? 'Продвинутый' :
                  request.level === 'professional' ? 'Профессионал' : 'Любой'
                }
              </div>
              <div className="info-item">
                <strong>Участников:</strong> {request.current_participants}/{request.max_participants}
              </div>
            </div>

            {request.requirements && (
              <div className="request-requirements-inline">
                <h3 className="requirements-title">Требования</h3>
                <p className="requirements-text">{request.requirements}</p>
              </div>
            )}

            <hr className="request-block-divider" />

            <div className="request-description-inline">
              <h3 className="description-title">Описание</h3>
              <p className="description-text">{request.description || '—'}</p>
            </div>
          </div>
        </div>
      </div>

      {!isCreator && user && !participating && (
        <div className="participate-section">
          <h2>Откликнуться на заявку</h2>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Напишите сообщение создателю заявки"
            rows="4"
          />
          <button onClick={handleParticipate} className="participate-button">
            Откликнуться
          </button>
        </div>
      )}

      {participating && (
        <div className="participating-message">
          Вы уже откликнулись на эту заявку
        </div>
      )}

      {canShowGroupChat && (
        <div className="chat-section">
          <button 
            onClick={handleStartGroupChat} 
            className="group-chat-button"
            disabled={creatingChat}
          >
            {creatingChat ? 'Создание чата...' : '💬 Чат активности'}
          </button>
          <p className="chat-info">
            Групповой чат со всеми участниками активности
          </p>
        </div>
      )}

      {!user && (
        <div className="login-prompt">
          <Link to="/login">Войдите</Link>, чтобы откликнуться на заявку
        </div>
      )}

      {(isCreator || isModerator) && (
        <>
          <div className="creator-actions">
            {isCreator && (
              <>
                <button onClick={handleEdit} className="btn-edit">
                  ✏️ Редактировать
                </button>
                <button onClick={() => {
                  setNewLocation({
                    location_name: request.location_name || '',
                    latitude: request.latitude || '',
                    longitude: request.longitude || '',
                    address: request.address || ''
                  })
                  setShowChangeLocationModal(true)
                }} className="btn-reschedule">
                  📍 Поменять место
                </button>
                {request.status === 'active' && (
                  <button onClick={() => setShowCancelModal(true)} className="btn-cancel-request">
                    ❌ Отменить
                  </button>
                )}
              </>
            )}
            {isModerator && (
              <button onClick={() => setShowDeleteModal(true)} className="btn-delete-request">
                🗑 Удалить заявку
              </button>
            )}
          </div>

          {isCreator && isEditing && (
            <EditRequestForm
              request={request}
              onCancel={handleCancelEdit}
              onSave={handleSaveEdit}
            />
          )}

          {showCancelModal && (
            <div className="modal-overlay" onClick={() => setShowCancelModal(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h3>Отменить заявку?</h3>
                <p>Все участники будут уведомлены об отмене.</p>
                <div className="modal-actions">
                  <button onClick={() => setShowCancelModal(false)} className="btn-cancel">
                    Нет
                  </button>
                  <button onClick={handleCancelRequest} className="btn-confirm">
                    Да, отменить
                  </button>
                </div>
              </div>
            </div>
          )}

          {showChangeLocationModal && (
            <div className="modal-overlay" onClick={() => setShowChangeLocationModal(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h3>Поменять место</h3>
                <div className="form-group">
                  <label>Место:</label>
                  <input
                    id="change_location_input"
                    type="text"
                    value={newLocation.location_name}
                    onChange={(e) => setNewLocation({ ...newLocation, location_name: e.target.value })}
                    placeholder="Начните вводить адрес или место"
                    required
                  />
                  <MapPicker
                    onSelect={(location) => {
                      if (location && location.latitude != null && location.longitude != null) {
                        setNewLocation({
                          location_name: location.name || location.address || '',
                          latitude: location.latitude,
                          longitude: location.longitude,
                          address: location.address || ''
                        })
                      }
                    }}
                    address={newLocation.location_name}
                    addressInputId="change_location_input"
                  />
                  {newLocation.address && (
                    <p className="address">{newLocation.address}</p>
                  )}
                </div>
                <div className="modal-actions">
                  <button onClick={() => setShowChangeLocationModal(false)} className="btn-cancel">
                    Отмена
                  </button>
                  <button onClick={handleChangeLocation} className="btn-confirm">
                    Сохранить
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="participants-section">
            <ParticipantsList 
              requestId={id} 
              onUpdate={loadRequest}
            />
          </div>
        </>
      )}
      
      {showDeleteModal && (
        <DeleteRequestModal
          request={request}
          onConfirm={handleDeleteRequest}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}

      {user && request && request.status === 'completed' && (() => {
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        const reqDate = new Date(request.date)
        reqDate.setHours(0, 0, 0, 0)
        return reqDate <= today
      })() && (
        <div className="reviews-section">
          <CreateReview request={request} onReviewCreated={loadRequest} />
        </div>
      )}
    </div>
  )
}

export default RequestDetailPage
