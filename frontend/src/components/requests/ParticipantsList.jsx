import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import './ParticipantsList.css'

function ParticipantsList({ requestId, onUpdate }) {
  const [participants, setParticipants] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadParticipants()
  }, [requestId])

  const loadParticipants = async () => {
    try {
      const response = await api.get(`/requests/${requestId}/participations/`)
      setParticipants(response.data || [])
    } catch (error) {
      console.error('Ошибка загрузки участников:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleViewProfile = (userId) => {
    navigate(`/profile/${userId}`)
  }

  const handleOpenChat = async (userId) => {
    try {
      const response = await api.post(`/chat/create/${userId}/`)
      navigate(`/chat/${response.data.id}`)
    } catch (error) {
      console.error('Ошибка открытия чата:', error)
      alert('Не удалось открыть чат')
    }
  }

  const handleExclude = async (participationId) => {
    if (!window.confirm('Вы уверены, что хотите исключить этого участника? Он больше не сможет участвовать в этой активности.')) {
      return
    }

    try {
      await api.post(`/requests/${requestId}/participations/${participationId}/exclude/`)
      loadParticipants()
      if (onUpdate) {
        onUpdate()
      }
    } catch (error) {
      console.error('Ошибка исключения участника:', error)
      alert('Не удалось исключить участника')
    }
  }

  const getStatusLabel = (status) => {
    const labels = {
      'pending': 'Ожидает подтверждения',
      'approved': 'Подтверждён',
      'rejected': 'Отклонён',
      'cancelled': 'Отменён',
      'excluded': 'Исключён'
    }
    return labels[status] || status
  }

  const getStatusClass = (status) => {
    return `status status-${status}`
  }

  if (loading) {
    return <div className="participants-list">Загрузка участников...</div>
  }

  const activeParticipants = participants.filter(p => p.status === 'approved')

  return (
    <div className="participants-list">
      <h3>Участники заявки</h3>
      {activeParticipants.length === 0 ? (
        <p className="no-participants">Пока нет участников</p>
      ) : (
        <div className="participants-grid">
          {activeParticipants.map(participation => (
            <div key={participation.id} className="participant-card">
              <div className="participant-header">
                <div className="participant-avatar">
                  {participation.user_profile?.photo ? (
                    <img 
                      src={participation.user_profile.photo} 
                      alt={participation.user?.username || 'Пользователь'} 
                    />
                  ) : (
                    <div className="avatar-placeholder">
                      {participation.user?.first_name?.[0] || participation.user?.username?.[0] || '?'}
                    </div>
                  )}
                </div>
                <div className="participant-info">
                  <h4>{participation.user?.first_name || participation.user?.username || 'Пользователь'}</h4>
                  <p className="participant-username">@{participation.user?.username}</p>
                  <span className={getStatusClass(participation.status)}>
                    {getStatusLabel(participation.status)}
                  </span>
                </div>
              </div>
              
              {participation.message && (
                <div className="participant-message">
                  <strong>Сообщение:</strong>
                  <p>{participation.message}</p>
                </div>
              )}

              <div className="participant-actions">
                <button 
                  onClick={() => handleViewProfile(participation.user?.id)} 
                  className="btn btn-profile"
                  title="Просмотр профиля"
                >
                  👤 Профиль
                </button>
                <button 
                  onClick={() => handleOpenChat(participation.user?.id)} 
                  className="btn btn-chat"
                  title="Написать сообщение"
                >
                  💬 Написать
                </button>
                {participation.status === 'approved' && (
                  <button 
                    onClick={() => handleExclude(participation.id)} 
                    className="btn btn-exclude"
                    title="Исключить участника"
                  >
                    ✕ Исключить
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ParticipantsList
