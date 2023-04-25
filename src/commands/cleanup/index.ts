import minimatch from 'minimatch'
import { Flags } from '@oclif/core'
import chalk from 'chalk'
import inquirer from 'inquirer'
import { lsFiles } from '../../utils/git/ls-files'
import Base from '../base'
import VarAliasFlag, { getVariableAliases } from '../../flags/var-alias'
import { Variable } from './types'
import { ENGINES } from '../../utils/refactor'
import { variablePrompt, variablePromptNoApi, variableTypePrompt, variableValuePrompt } from '../../ui/prompts'
import { spawn } from 'child_process'

export default class Cleanup extends Base {
    static hidden = false
    runsInRepo = true

    static description = 'Replace a DevCycle variable with a static value in the current version of your code. ' +
        'Currently only JavaScript is supported.' 
    static examples = [
        '<%= config.bin %> <%= command.id %>',
        '<%= config.bin %> <%= command.id %> my-variable-key --value true --type Boolean',
        '<%= config.bin %> <%= command.id %> some-var --value "My Custom Name" --type String',
    ]

    static args = [
        {
            name: 'key',
            description: 'Key of variable to replace.'
        }
    ]

    static flags = {
        ...Base.flags,
        'value': Flags.string({
            description: 'Value to use in place of variable.'
        }),
        'type': Flags.string({
            description: 'The type of the value that will be replacing the variable. ' +
                'Valid values include: String, Boolean, Number, JSON',
            options: ['String', 'Boolean', 'Number', 'JSON']
        }),
        'include': Flags.string({
            description: 'Files to include when scanning for variables to cleanup. ' +
                'By default all files are included. ' +
                'Accepts multiple glob patterns.',
            multiple: true
        }),
        'exclude': Flags.string({
            description: 'Files to exclude when scanning for variables to cleanup. ' +
                'By default all files are included. ' +
                'Accepts multiple glob patterns.',
            multiple: true
        }),
        'output': Flags.string({
            description: 'Where the refactored code will be output. By default it overwrites the source file.',
            options: ['console', 'file'],
            default: 'file'
        }),
        'var-alias': VarAliasFlag
    }

    public async run(): Promise<void> {
        const { flags, args } = await this.parse(Cleanup)
        const codeInsightsConfig = this.repoConfig?.codeInsights || {}
        const apiAuth = this.token && this.projectKey
            ? {
                token: this.token,
                projectKey: this.projectKey
            } : undefined

        const variable = {
            key: args.key,
            value: flags.value,
            type: flags.type
        } as Variable

        if (!variable.key) {
            if (apiAuth) {
                try {
                    const input = await inquirer.prompt([variablePrompt], apiAuth)
                    variable.key = input.variable.key
                } catch {} // eslint-disable-line no-empty
            }
            if (!variable.key) {
                const input = await inquirer.prompt([variablePromptNoApi])
                variable.key = input.variable
            }
        }
        if (!variable.type) {
            const input = await inquirer.prompt([variableTypePrompt])
            variable.type = input.type
        }
        if (!variable.value) {
            const input = await inquirer.prompt([variableValuePrompt])
            variable.value = input.value
        }

        const includeFile = (filepath: string) => {
            const includeGlobs = flags['include'] || codeInsightsConfig.includeFiles
            return includeGlobs
                ? includeGlobs.some((glob) => minimatch(filepath, glob, { matchBase: true }))
                : true
        }

        const excludeFile = (filepath: string) => {
            const excludeGlobs = flags['exclude'] || codeInsightsConfig.excludeFiles
            return excludeGlobs
                ? excludeGlobs.some((glob) => minimatch(filepath, glob, { matchBase: true }))
                : false
        }

        const aliases = new Set()
        Object.entries(getVariableAliases(flags, this.repoConfig)).forEach(([alias, variableKey]) => {
            if (variableKey === args.key) aliases.add(alias)
        })

        const files = lsFiles().filter((filepath) => includeFile(filepath) && !excludeFile(filepath))

        if (!files.length) {
            this.warn('No files found to process.')
            return
        }

        files.forEach((filepathToRefactor) => {
            const options = {
                output: flags.output || 'file',
                aliases
            }

            const fileExtension = filepathToRefactor?.split('.').pop() ?? ''
            if (!ENGINES[fileExtension]) return
            ENGINES[fileExtension].forEach(([command, engineFilePath]) => {
                try {
                    const engineArgs = [filepathToRefactor, JSON.stringify(variable), JSON.stringify(options)]
                    const childProcess = spawn(command, [engineFilePath, ...engineArgs])
                    childProcess.stdout.on('data', (msg) => console.log(msg.toString()))
                    childProcess.stdout.on('message', (msg) => console.log(msg.toString()))
                    childProcess.on('error', (err: Error & { code: string }) => {
                        console.warn(chalk.yellow(`Error refactoring ${filepathToRefactor}`))
                        if (err.code === 'ENOENT') {
                            console.warn(`Could not find ${command} executable. Is it installed?`)
                        } else {
                            console.error(err.toString())
                        }
                    })
                } catch (err: any) {
                    console.warn(chalk.yellow(`Error refactoring ${filepathToRefactor}`))
                    console.warn(`\t${err.message}`)
                }
            })
        })
    }
}
