import './RequestCard.css'

function RequestCard({ request, hideDescription = false }) {
  const formatAddress = (address) => {
    if (!address) return 'Место не указано'
    
    const parts = address.split(',').map(p => p.trim())
    
    let settlement = ''
    let street = ''
    let house = ''
    
    for (let i = parts.length - 1; i >= 0; i--) {
      const part = parts[i]
      
      if (!house && part.match(/^\d+[а-яА-ЯсС]?$/)) {
        house = part
        continue
      }
      
      if (!street && (part.match(/улица|ул\./i) || 
          (part.match(/^[А-ЯЁ][а-яё]+$/i) && !settlement && !house))) {
        street = part.replace(/улица\s*/i, '').replace(/ул\.\s*/i, '').trim()
        continue
      }
      
      if (!settlement) {
        if (part.match(/посёлок городского типа|поселок городского типа/i)) {
          const match = part.match(/(?:посёлок городского типа|поселок городского типа)\s+(.+)/i)
          if (match) {
            settlement = 'Пгт ' + match[1].trim()
          }
        } else if (part.match(/посёлок|поселок|город|село|деревня/i)) {
          const match = part.match(/(?:посёлок|поселок|город|село|деревня)\s+(.+)/i)
          if (match) {
            settlement = match[1].trim()
          }
        } else if (part.match(/^[А-ЯЁ][а-яё]+$/i) && !street && !house) {
          settlement = part
        }
      }
    }
    
    if (settlement && street && house) {
      return `${settlement}, ${street} ${house}`
    }
    if (settlement && street) {
      return `${settlement}, ${street}`
    }
    if (settlement) {
      return settlement
    }
    
    return address
      .replace(/посёлок городского типа/gi, 'Пгт')
      .replace(/поселок городского типа/gi, 'Пгт')
      .replace(/улица/gi, 'ул.')
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const reqDate = new Date(date)
    reqDate.setHours(0, 0, 0, 0)
    
    if (reqDate.getTime() === today.getTime()) {
      return 'Сегодня'
    }
    
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    if (reqDate.getTime() === tomorrow.getTime()) {
      return 'Завтра'
    }
    
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
    })
  }

  const getStatusBadge = () => {
    if (request.status === 'active') {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const reqDate = new Date(request.date)
      reqDate.setHours(0, 0, 0, 0)
      
      if (reqDate < today) {
        return <span className="status-badge status-past">Прошедшая</span>
      }
      return <span className="status-badge status-active">Активна</span>
    }
    
    const statusLabels = {
      'completed': 'Завершена',
      'cancelled': 'Отменена',
      'filled': 'Набрана',
      'pending': 'Ожидает'
    }
    
    return <span className="status-badge status-other">{statusLabels[request.status] || request.status}</span>
  }

  return (
    <div className="request-card">
      {request.photos && request.photos.length > 0 && (
        <div className="card-photo">
          <img src={request.photos[0]} alt={request.title} />
        </div>
      )}
      <div className="card-header">
        <h3>{request.title}</h3>
        {getStatusBadge()}
      </div>
      <p className="request-activity">{request.activity?.name || 'Активность не указана'}</p>
      <div className="request-info">
        <p className="request-location">
          📍 {formatAddress(request.location_name || request.address)}
        </p>
        <p className="request-date">
          📅 {formatDate(request.date)} в {request.time}
        </p>
        <p className="request-participants">
          👥 {request.current_participants || 0}/{request.max_participants} участников
        </p>
      </div>
      {!hideDescription && request.description && (
        <p className="request-description">
          {request.description.length > 100 
            ? request.description.substring(0, 100) + '...' 
            : request.description}
        </p>
      )}
    </div>
  )
}

export default RequestCard

