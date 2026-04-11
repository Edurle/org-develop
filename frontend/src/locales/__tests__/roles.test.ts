import { describe, it, expect } from 'vitest'
import en from '../en.json'
import zhCN from '../zh-CN.json'

const roleKeys = [
  'team.teamAdmin',
  'team.productOwner',
  'team.designer',
  'team.developer',
  'team.tester',
  'team.viewer',
]

const memberKeys = [
  'team.members',
  'team.noMembers',
  'team.addMember',
  'team.removeMember',
  'team.confirmRemove',
  'team.confirmRemoveMsg',
  'team.updateRole',
  'team.searchUsersPlaceholder',
  'team.noUsersFound',
  'team.selectUser',
  'team.role',
  'team.joined',
  'team.failedLoadMembers',
  'team.failedAddMember',
  'team.failedRemoveMember',
  'team.failedUpdateRole',
  'team.loadingMembers',
  'team.adding',
  'team.remove',
]

function resolve(obj: any, key: string): any {
  const parts = key.split('.')
  let current: any = obj
  for (const part of parts) {
    current = current[part]
  }
  return current
}

describe('i18n role and member keys', () => {
  it.each(roleKeys)('en.json has key %s', (key) => {
    const val = resolve(en, key)
    expect(val).toBeDefined()
    expect(typeof val).toBe('string')
  })

  it.each(roleKeys)('zh-CN.json has key %s', (key) => {
    const val = resolve(zhCN, key)
    expect(val).toBeDefined()
    expect(typeof val).toBe('string')
  })

  it.each(memberKeys)('en.json has key %s', (key) => {
    const val = resolve(en, key)
    expect(val).toBeDefined()
    expect(typeof val).toBe('string')
  })

  it.each(memberKeys)('zh-CN.json has key %s', (key) => {
    const val = resolve(zhCN, key)
    expect(val).toBeDefined()
    expect(typeof val).toBe('string')
  })
})
