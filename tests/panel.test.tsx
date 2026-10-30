import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'

const OPTIONS = { user: 'yash', relayUrl: 'http://relay', teamToken: 't' }

const PANE = {
  plugin: 'team-handoff',
  component: 'Pane',
  requestId: 'team',
  surface: 'terminal',
  props: {
    title: '👥 Team',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

type Sent = { path: string; body: Record<string, unknown> }

/** Stands in for the engine and the relay: inbox messages, a pane that is shown or not. */
function engine(on: On, inbox: Record<string, unknown>[], panel: { isOpen: boolean }) {
  const sent: Sent[] = []
  const submitted: string[] = []
  const members = [
    { user: 'yash', repo: 'app', branch: 'main', status: '', online: true, lastSeen: 0 },
    { user: 'vatsal', repo: 'app', branch: 'bugfix/appicon', status: '', online: true, lastSeen: 0 },
  ]
  const reply = (body: unknown) => ({ value: { status: 200, ok: true, headers: {}, text: JSON.stringify(body) } })

  on('http.fetch', (_, e) => {
    const path = new URL(e.url).pathname
    const body = e.init?.body ? (JSON.parse(e.init.body) as Record<string, unknown>) : {}
    if (e.init?.method === 'POST') sent.push({ path, body })
    if (path === '/members') return reply({ members })
    if (path === '/inbox') {
      const acked = new Set(sent.filter(s => s.path === '/ack').map(s => s.body.id))
      return reply({ messages: inbox.filter(m => !acked.has(m.id)) })
    }
    if (path === '/messages') return reply({ id: 'x', knownRecipient: true })
    return reply({ ok: true })
  })
  on('ui.panes', () => ({
    value: panel.isOpen ? [{ id: 'team', title: '👥 Team', isShown: true, isFocused: false, isPlaced: true }] : [],
  }))
  on('ui.open', () => {
    panel.isOpen = true
    return { value: { isPlaced: true } }
  })
  on('ui.close', () => {
    panel.isOpen = false
    return { value: undefined }
  })
  on('prompt.submit', (_, e) => {
    submitted.push(e.text)
    return { text: e.text }
  })
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__team-handoff__${e.name}` } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  mock.env(on, { HOME: '/home/test' })
  return { sent, submitted }
}

const chat = { id: 'c1', kind: 'chat', from: 'vatsal', to: 'yash', title: 'hi there', body: '', createdAt: 0 }
const ask = { id: 'a1', kind: 'ask', from: 'vatsal', to: 'yash', title: 'what branch?', body: '', group: 'g1', createdAt: 0 }

test('the panel shows who is online and the chat', { options: OPTIONS }, async ($, on) => {
  const clock = mock.clock(on)
  engine(on, [chat], { isOpen: true })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await clock.advance(12_000)

  const ui = await $.ui.mount(PANE)
  expect((await ui.find({ type: 'Text', text: /bugfix\/appicon/ }))?.text).toMatch(/vatsal/)
  expect((await ui.find({ type: 'Text', text: /hi there/ }))?.text).toMatch(/vatsal/)
  await ui.unmount()
})

// What the person typing /team-panel at the prompt sends.
const TEAM_PANEL = {
  command: 'team-panel',
  args: '',
  origin: { kind: 'composer' },
  presentation: { isFullscreen: false, columns: 160 },
} as const

test('/team-panel opens the panel, then closes it', { options: OPTIONS }, async ($, on) => {
  const panel = { isOpen: false }
  engine(on, [], panel)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  expect((await $.command.run(TEAM_PANEL)).text).toMatch(/open/)
  expect(panel.isOpen).toBe(true)
  expect((await $.command.run(TEAM_PANEL)).text).toMatch(/closed/)
  expect(panel.isOpen).toBe(false)
})

test('with the panel open, a question waits as a card until Allow is pressed', { options: OPTIONS }, async ($, on) => {
  const clock = mock.clock(on)
  const { sent, submitted } = engine(on, [ask], { isOpen: true })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await clock.advance(12_000)

  // No answer yet: the card waits, nothing was acknowledged or submitted.
  expect(sent.some(s => s.path === '/ack')).toBe(false)
  expect(submitted).toEqual([])

  const ui = await $.ui.mount(PANE)
  expect((await ui.find({ type: 'Text', text: /what branch\?/ }))?.text).toMatch(/vatsal asks your Claude/)
  await ui.press({ key: 'a1-Allow' })

  expect(sent.some(s => s.path === '/ack' && s.body.id === 'a1')).toBe(true)
  expect(sent.some(s => s.path === '/messages' && s.body.kind === 'typing')).toBe(true)
  expect(submitted[0]).toMatch(/^\[team-ask a1\]/)
  await ui.unmount()
})

test('Later keeps a request waiting; a decision is kept as a record', { options: OPTIONS }, async ($, on) => {
  const clock = mock.clock(on)
  const { sent } = engine(on, [ask], { isOpen: true })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await clock.advance(12_000)

  const ui = await $.ui.mount(PANE)
  await ui.press({ key: 'a1-Later' })
  expect(sent.some(s => s.path === '/ack')).toBe(false)
  expect((await ui.find({ type: 'Text', text: /1 waiting/ }))?.text).toMatch(/@yash/)

  await ui.press({ key: 'a1-Decline' })
  expect(sent.some(s => s.path === '/ack' && s.body.id === 'a1')).toBe(true)
  expect(sent.some(s => s.path === '/messages' && s.body.kind === 'answer')).toBe(true)
  expect((await ui.find({ key: 'a1-row' }))?.props.label).toMatch(/✗ declined/)
  expect(await ui.find({ key: 'a1-Allow' })).toBeUndefined()
  await ui.unmount()
})

test('an invite code joins as the invited handle', async ($, on) => {
  const written: string[] = []
  const redeemed: unknown[] = []
  mock.clock(on)
  on('http.fetch', (_, e) => {
    if (e.url.endsWith('/redeem')) {
      redeemed.push({ url: e.url, body: JSON.parse(e.init?.body ?? '{}') })
      return { value: { status: 200, ok: true, headers: {}, text: JSON.stringify({ user: 'vatsal', token: 'tok' }) } }
    }
    return { value: { status: 200, ok: true, headers: {}, text: '{}' } }
  })
  on('fs.exists', () => ({ value: false }))
  on('fs.write', (_, e) => {
    written.push(e.text)
    return { value: undefined }
  })
  on('process.run', () => ({ value: { exitCode: 0, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__team-handoff__${e.name}` } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  mock.env(on, { HOME: '/home/test' })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const code = 'tmh1-' + btoa('http://192.168.1.5:8787|K7P2-9QXA').replace(/=+$/, '')
  const joined = await $.tool.call({ tool: 'mcp__team-handoff__team_join', code })
  expect(String(joined.text)).toMatch(/Joined as @vatsal/)
  expect(redeemed).toEqual([{ url: 'http://192.168.1.5:8787/redeem', body: { code: 'K7P2-9QXA' } }])
  expect(JSON.parse(written[0] ?? '{}')).toMatchObject({ user: 'vatsal', relayUrl: 'http://192.168.1.5:8787', teamToken: 'tok' })
})

test('after a restart, the relay address saved by an invite is used', async ($, on) => {
  const urls: string[] = []
  mock.clock(on)
  on('http.fetch', (_, e) => {
    urls.push(e.url)
    return { value: { status: 200, ok: true, headers: {}, text: JSON.stringify({ members: [] }) } }
  })
  on('fs.exists', () => ({ value: true }))
  on('fs.read', () => ({
    value: JSON.stringify({ user: 'yuvraj', relayUrl: 'http://192.168.1.5:8787', teamToken: 'tok' }),
  }))
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__team-handoff__${e.name}` } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  mock.env(on, { HOME: '/home/test' })

  // No options given: the manifest's defaults apply, as for a teammate who never opened /config.
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(urls.length).toBeGreaterThan(0)
  expect(urls.every(url => url.startsWith('http://192.168.1.5:8787/'))).toBe(true)
})
