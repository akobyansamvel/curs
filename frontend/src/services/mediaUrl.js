/**
 * Нормализует URL медиа-файла (фото профиля, фото заявок).
 * Относительные пути /media/... проксируются на бэкенд через Vite (dev) или отдаются тем же хостом (production).
 * Абсолютные URL и data: URL возвращаются как есть.
 */
export function getMediaUrl(url) {
  if (!url || typeof url !== 'string') return ''
  const trimmed = url.trim()
  if (!trimmed) return ''
  // data: URL (превью после выбора файла) — как есть
  if (trimmed.startsWith('data:')) return trimmed
  // Абсолютный URL
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed
  // Относительный от корня — дополняем ведущим слэшем если нет
  if (trimmed.startsWith('media/')) return `/${trimmed}`
  return trimmed
}
