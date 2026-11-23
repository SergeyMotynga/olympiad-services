export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

export async function request(path, { method = 'GET', token, body } = {}) {
  const headers = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body: JSON.stringify(body),
      cache: 'no-store',
      signal: AbortSignal.timeout(8000),
    })
  } catch {
    throw new ApiError('Сервис доступа недоступен. Проверь запуск бэкенда и повтори попытку.')
  }

  if (response.status === 204) return
  if (response.ok) return response.json()

  const { detail } = await response.json().catch(() => ({}))
  const messages = {
    401: token ? 'Сессия завершилась. Войди снова.' : 'Неверный логин или пароль.',
    404: 'Не найдено.',
    422: 'Проверь значения в полях формы.',
  }
  const message = response.status === 404 ? messages[404] : (
    typeof detail === 'string' ? detail : messages[response.status]
  )
  throw new ApiError(
    message ?? 'Сервис доступа недоступен. Повтори попытку.',
    response.status,
  )
}
