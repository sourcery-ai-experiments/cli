import { readFileSync } from 'fs'
import { resolve } from 'path'
import { load } from 'js-yaml'
import { UserConfigFromFile } from '../../types/configFile'

export function getConfigPath(): string {
    const defaultConfigPath = resolve('.devcycle/config.yaml')
    const savedConfigPath = process.env.CONFIG_PATH ? resolve(process.env.CONFIG_PATH) : defaultConfigPath
    return savedConfigPath
}

export function loadUserConfigFromFile(configPath: string): UserConfigFromFile {
    const userConfigYaml = readFileSync(configPath, 'utf8')
    const loadedConfig = load(userConfigYaml) as UserConfigFromFile
    return loadedConfig || {}
}