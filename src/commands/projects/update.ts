import { Flags } from '@oclif/core'
import { fetchProjects, Project, updateProject, UpdateProjectParams } from '../../api/projects'
import Base from '../base'
import { CurrentSettings } from '../../ui/prompts/projectPrompts'
import { descriptionPrompt, namePrompt, colorPrompt, settingsPrompt } from '../../ui/prompts'
import { EdgeDBSettings, OptInSettings, ProjectSettings } from '../../api/projectSettings'
import { getConfigPath, loadUserConfigFromFile } from '../../utils/config/configUtils'
import inquirer from 'inquirer'

export default class UpdateProject extends Base {
    
  static description = 'Update the project settings';

  static flags = {
      ...Base.flags,
      help: Flags.help({ char: 'h' }),
      name: Flags.string({ description: 'Project name' }),
      description: Flags.string({ description: 'Project description' }),
      color: Flags.string({ description: 'Project color (Hex color code)' }),
  };

  static args = [
      { name: 'projectKey', required: false, description: 'The project key' }
  ]

  authRequired = true;

  async run(): Promise<void> {
      const { args, flags } = await this.parse(UpdateProject)

      let projectKey = args.projectKey

      if (!projectKey) {
          const currentProjectKey = this.getCurrentProjectKey()
          console.log(currentProjectKey)
          const useCurrentProjectKey = await inquirer.prompt({
              type: 'confirm',
              name: 'useCurrent',
              message: `No project key provided. Would you like to use the current project key (${currentProjectKey})?`,
          })

          if (useCurrentProjectKey.useCurrent) {
              projectKey = currentProjectKey
          } else {
              const enteredProjectKey = await inquirer.prompt({
                  type: 'input',
                  name: 'enteredKey',
                  message: 'Please enter a project key:',
                  validate: (value: string) => {
                      if (value.trim()) return true
                      return 'A valid project key is required.'
                  },
              })
              projectKey = enteredProjectKey.enteredKey
          }
      }

      const currentProject = await this.getCurrentProject(projectKey)
      if (!currentProject) {
          this.writer.showResults(`Project with key ${projectKey} not found.`)
          return
      }
  
      const options = ['name', 'description', 'color', 'edgeDB', 'optIn']
  
      if (Object.values(flags).some((flag) => flag !== undefined)) {
          const params: UpdateProjectParams = {
              name: flags.name,
              description: flags.description,
              color: flags.color,
          }
  
          const updatedProject = await updateProject(this.token, projectKey, params)
          this.writer.showResults(`Project ${updatedProject.key} has been updated.`)
      } else {
          const selectedOption = await inquirer.prompt({
              type: 'list',
              name: 'option',
              message: 'Select the setting you want to modify:',
              choices: [...options, 'Cancel'],
          })
  
          if (selectedOption.option === 'Cancel') {
              return
          }
  
          const updatedProject = await this.updateOption(selectedOption.option, currentProject)
          this.writer.showResults(`Project ${updatedProject.key} has been updated.`)
      }
  }

  private getCurrentSettings(project: Project): CurrentSettings {
      const { edgeDB, optIn } = project.settings as ProjectSettings
  
      return {
          edgeDB: { enabled: edgeDB.enabled },
          optIn,
      }
  }
  
  private getCurrentProjectKey(): string | undefined {
      const configPath = getConfigPath()
      const userConfig = loadUserConfigFromFile(configPath)
      return userConfig && userConfig.project
  }

  private async getCurrentProject(projectKey: string): Promise<Project | null> {
      const projects = await fetchProjects(this.token)
      return projects.find((project) => project.key === projectKey) || null
  }
  
  private async updateOption(option: string, currentProject: Project): Promise<Project> {
      const projectKey = currentProject.key
      switch (option) {
          case 'name': {
              const name = await namePrompt(`Current name: ${currentProject.name}`)
              return await updateProject(this.token, projectKey, { name: name.name })
          }
          case 'description': {
              const description = await descriptionPrompt(`Current description: ${currentProject.description}`)
              return await updateProject(this.token, projectKey, { description: description.description })
          }
          case 'color': {
              const color = await colorPrompt(`Current color: ${currentProject.color}`)
              return await updateProject(this.token, projectKey, { color: color.color })
          }
          case 'edgeDB': {
              const edgeDBEnabled = await inquirer.prompt({
                  type: 'confirm',
                  name: 'enabled',
                  message: `Enable edgeDB? (current: ${currentProject.settings?.edgeDB?.enabled ?? false})`,
              })
              return await updateProject(this.token, projectKey, {
                  settings: {
                      edgeDB: { enabled: edgeDBEnabled.enabled },
                      optIn: currentProject.settings?.optIn ?? {},
                  },
              })
          }
          case 'optIn': {
              const currentSettings = this.getCurrentSettings(currentProject)
              const optInSettings = await settingsPrompt(currentSettings)
        
              if (optInSettings) {
                  const { edgeDB, optIn } = optInSettings
                  return await updateProject(this.token, projectKey, {
                      settings: {
                          edgeDB: edgeDB ?? currentProject.settings?.edgeDB ?? new EdgeDBSettings(),
                          optIn: optIn as OptInSettings,
                      },
                  })
              } else {
                  this.writer.showResults(`No changes made to project ${projectKey}.`)
                  return currentProject
              }
          }
          default:
              throw new Error('Invalid option selected.')
      }
  }
}
