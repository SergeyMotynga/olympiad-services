import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { request } from './api'
import './styles.css'

const sessionKey = 'olympiad-access-session'
const roleNames = {
  admin: 'Администратор',
  author: 'Составитель',
  representative: 'Представитель',
  reviewer: 'Проверяющий',
}
const operationGroups = {
  'Доступ и роли': {
    'roles:list': 'Просмотр ролей',
    'accounts:create': 'Создание аккаунтов',
    'accounts:change_role': 'Смена роли аккаунта',
  },
  'Задачи и печать': {
    'tasks:list': 'Просмотр задач',
    'tasks:create': 'Создание задач',
    'tasks:update': 'Редактирование задач',
    'tasks:print': 'Печать материалов',
  },
  'Приём бланков': {
    'submissions:open': 'Открытие приёма',
    'submissions:list': 'Просмотр истории',
    'submissions:create': 'Отправка бланков',
    'submissions:update': 'Исправление записи',
  },
}
const dateFormat = new Intl.DateTimeFormat('ru', {
  dateStyle: 'long',
  timeStyle: 'short',
})

function readSession() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(sessionKey))
    return saved?.access_token ? saved : null
  } catch {
    return null
  }
}

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">∑</span>
      <span>Математические<br />игры</span>
    </div>
  )
}

function Geometry() {
  return (
    <div className="geometry" aria-hidden="true">
      <div className="geometry-orbit" />
      <div className="geometry-square" />
      <div className="geometry-ring" />
      <div className="geometry-core" />
      <span className="geometry-node geometry-node-top" />
      <span className="geometry-node geometry-node-bottom" />
    </div>
  )
}

function Login({ busy, error, onLogin }) {
  return (
    <main className="login-page">
      <div className="login-header"><Brand /></div>
      <div className="login-layout">
        <section className="login-art">
          <Geometry />
          <div className="login-art-text">
            <span>Кабинет организатора</span>
            <p>Математические<br />игры</p>
          </div>
        </section>
        <section className="login-content">
          <h1>Вход в кабинет</h1>
          <p>Введи логин и пароль, которые выдал администратор.</p>
          <form onSubmit={(event) => {
            event.preventDefault()
            const fields = new FormData(event.currentTarget)
            onLogin({ login: fields.get('login').trim(), password: fields.get('password') })
          }}>
            <label>Логин<input name="login" autoComplete="username" disabled={busy} required /></label>
            <label>Пароль<input name="password" type="password" autoComplete="current-password" disabled={busy} required /></label>
            {error && <p className="notice error" role="alert">{error}</p>}
            <button className="primary login-submit" disabled={busy}>
              {busy ? 'Входим…' : 'Войти'} <span aria-hidden="true">↗</span>
            </button>
          </form>
        </section>
      </div>
    </main>
  )
}

function Overview({ account, session, onRefresh, busy }) {
  const known = new Set(Object.values(operationGroups).flatMap(Object.keys))
  const unknown = account.operations.filter((operation) => !known.has(operation))
  return (
    <>
      <section className="hero">
        <Geometry />
        <div className="hero-content">
          <span className="hero-label">Доступ и роли</span>
          <h1>Личный кабинет</h1>
          <p>Текущая сессия и права твоего аккаунта.</p>
        </div>
      </section>
      <div className="summary">
        <div className="card session-card">
          <span className="caption">Сессия</span>
          <strong><span className="active-dot" /> Активна</strong>
          <span className="muted">До {dateFormat.format(new Date(session.expires_at))}</span>
        </div>
        <div className="card session-card">
          <span className="caption">Доступные операции</span>
          <strong>{account.operations.length}</strong>
          <span className="muted">По текущей роли</span>
        </div>
        <div className="card session-card">
          <span className="caption">Аккаунт</span>
          <strong>{session.login}</strong>
          <code title={account.account_id}>{account.account_id}</code>
        </div>
      </div>
      <section className="card permissions">
        <div className="section-heading">
          <h2>Права доступа</h2>
          <button className="secondary" onClick={onRefresh} disabled={busy}>Обновить права</button>
        </div>
        {account.operations.length === 0 && <p className="muted">У текущей роли нет доступных операций.</p>}
        <div className="permission-groups">
          {Object.entries(operationGroups).map(([group, operations]) => {
            const allowed = Object.keys(operations).filter((operation) => account.operations.includes(operation))
            return allowed.length > 0 && (
              <div key={group}>
                <h3>{group}</h3>
                <ul>{allowed.map((operation) => <li key={operation}>{operations[operation]}</li>)}</ul>
              </div>
            )
          })}
          {unknown.length > 0 && (
            <div>
              <h3>Другие операции</h3>
              <ul>{unknown.map((operation) => <li key={operation}><code>{operation}</code></li>)}</ul>
            </div>
          )}
        </div>
      </section>
    </>
  )
}

function RoleField({ roles, disabled }) {
  return (
    <label>Роль
      <select name="role_id" disabled={disabled} required defaultValue="">
        <option value="" disabled>Выбери роль</option>
        {roles.map((role) => <option key={role.id} value={role.id}>{roleNames[role.code] ?? role.name}</option>)}
      </select>
    </label>
  )
}

function Accounts({ account, roles, busy, run, send, refresh }) {
  const [targetId, setTargetId] = useState('')
  const [result, setResult] = useState(null)
  const canCreate = account.operations.includes('accounts:create')
  const canChange = account.operations.includes('accounts:change_role')

  function submit(event, changeRole) {
    event.preventDefault()
    const form = event.currentTarget
    const fields = new FormData(form)
    const roleId = Number(fields.get('role_id'))
    const id = targetId.trim()
    setResult(null)
    run(async () => {
      const saved = changeRole
        ? await send(`/accounts/${encodeURIComponent(id)}/role`, { method: 'PATCH', body: { role_id: roleId } })
        : await send('/accounts', {
          method: 'POST',
          body: { login: fields.get('login').trim(), password: fields.get('password'), role_id: roleId },
        })
      setResult({ saved, message: changeRole ? 'Роль изменена' : 'Аккаунт создан' })
      setTargetId(saved.id)
      form.reset()
      if (changeRole && saved.id === account.account_id) await refresh()
    })
  }

  return (
    <section className="accounts-page">
      <header className="page-intro">
        <h1>Аккаунты</h1>
        <p>Создавай аккаунты и назначай роли участникам.</p>
      </header>
      {busy && roles.length === 0 && <p className="muted" role="status">Загружаем роли…</p>}
      {roles.length > 0 && (
        <section className="card role-card">
          <h2>Роли</h2>
          <ul className="role-list">
            {roles.map((role) => <li key={role.id}>{roleNames[role.code] ?? role.name}</li>)}
          </ul>
        </section>
      )}
      <div className="account-forms">
        {canCreate && (
          <section className="card">
            <h2>Новый аккаунт</h2>
            <form onSubmit={(event) => submit(event, false)} autoComplete="off">
              <label>Логин
                <input name="login" placeholder="Например, task.author" maxLength={32} disabled={busy} required />
              </label>
              <label>Пароль
                <input name="password" type="password" autoComplete="new-password" minLength={8} disabled={busy} required />
                <span className="hint">От 8 символов, до 72 байт в UTF-8</span>
              </label>
              <RoleField roles={roles} disabled={busy || roles.length === 0} />
              <button className="primary" disabled={busy || roles.length === 0}>Создать аккаунт</button>
            </form>
          </section>
        )}
        {canChange && (
          <section className="card">
            <h2>Смена роли</h2>
            <form onSubmit={(event) => submit(event, true)}>
              <label>ID аккаунта
                <input value={targetId} onChange={(event) => setTargetId(event.target.value)} disabled={busy} required />
                <span className="hint">Скопируй ID из кабинета нужного аккаунта</span>
              </label>
              <RoleField roles={roles} disabled={busy || roles.length === 0} />
              <button className="primary" disabled={busy || roles.length === 0}>Изменить роль</button>
            </form>
          </section>
        )}
      </div>
      {result && (
        <div className="notice success" role="status">
          <strong>{result.message} · {result.saved.login}</strong>
          <code>{result.saved.id}</code>
        </div>
      )}
    </section>
  )
}

function App() {
  const [session, setSession] = useState(readSession)
  const [account, setAccount] = useState(null)
  const [roles, setRoles] = useState([])
  const [page, setPage] = useState('overview')
  const [busy, setBusy] = useState(Boolean(session))
  const [error, setError] = useState('')

  function clearSession() {
    sessionStorage.removeItem(sessionKey)
    setSession(null)
    setAccount(null)
    setRoles([])
    setPage('overview')
  }

  async function run(action) {
    setBusy(true)
    setError('')
    try {
      await action()
    } catch (failure) {
      if (session && failure.status === 401) clearSession()
      setError(failure.message)
    } finally {
      setBusy(false)
    }
  }

  function send(path, options) {
    return request(path, { ...options, token: session.access_token })
  }

  async function loadAccount(credentials) {
    const current = await request('/auth/me', { token: credentials.access_token })
    setAccount(current)
    if (!current.operations.includes('roles:list')) {
      setRoles([])
      setPage('overview')
    }
    return current
  }

  function refresh() {
    return loadAccount(session)
  }

  useEffect(() => {
    if (session) run(refresh)
  }, [])

  function login(credentials) {
    run(async () => {
      const issued = await request('/auth/login', { method: 'POST', body: credentials })
      const next = { ...issued, login: credentials.login.toLowerCase() }
      sessionStorage.setItem(sessionKey, JSON.stringify(next))
      setSession(next)
      await loadAccount(next)
    })
  }

  function openAccounts() {
    setPage('accounts')
    run(async () => {
      const current = await refresh()
      if (current.operations.includes('roles:list')) setRoles(await send('/roles'))
    })
  }

  function logout() {
    run(async () => {
      await send('/auth/logout', { method: 'POST' })
      clearSession()
    })
  }

  if (!session) return <Login busy={busy} error={error} onLogin={login} />

  const showAccounts = account?.operations.includes('roles:list')
  return (
    <div className="workspace">
      <aside className="sidebar">
        <Brand />
        <nav aria-label="Кабинет">
          <button aria-current={page === 'overview' ? 'page' : undefined} onClick={() => setPage('overview')} disabled={busy}>
            <span aria-hidden="true">◈</span> Обзор
          </button>
          {showAccounts && (
            <button aria-current={page === 'accounts' ? 'page' : undefined} onClick={openAccounts} disabled={busy}>
              <span aria-hidden="true">⊞</span> Аккаунты
            </button>
          )}
        </nav>
        <div className="sidebar-footer">
          <span className="avatar" aria-hidden="true">{session.login.slice(0, 2).toUpperCase()}</span>
          <span>{session.login}</span>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span>Кабинет организатора</span>
          <button className="secondary" onClick={logout} disabled={busy}>Выйти <span aria-hidden="true">↗</span></button>
        </header>
        <div className="content">
          {error && <p className="notice error" role="alert">{error}</p>}
          {!account && (
            <div className="card">
              {busy ? <p role="status">Проверяем сессию…</p> : (
                <button className="secondary" onClick={() => run(refresh)}>Проверить сессию</button>
              )}
            </div>
          )}
          {account && page === 'overview' && (
            <Overview account={account} session={session} onRefresh={() => run(refresh)} busy={busy} />
          )}
          {account && showAccounts && page === 'accounts' && (
            <Accounts account={account} roles={roles} run={run} send={send} refresh={refresh} busy={busy} />
          )}
        </div>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
