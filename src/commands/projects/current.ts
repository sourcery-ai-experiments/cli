import { Flags } from '@oclif/core'
import { fetchProjects } from '../../api/projects'
import Base from '../base'
import { getConfigPath, loadUserConfigFromFile } from '../../utils/config/configUtils'

export default class ProjectsCurrent extends Base {
  static description = 'Display the current project key'
  static aliases = ['pc', 'project']
  static flags = {
      ...Base.flags,
      verbose: Flags.boolean({ char: 'v', description: 'Show more info about the current project' }),
  }

  async run(): Promise<void> {
      const { flags } = await this.parse(ProjectsCurrent) // Add this line to parse the input flags
  
      try {
          const configPath = getConfigPath()
          const userConfig = loadUserConfigFromFile(configPath)
          if (userConfig && userConfig.project) {
              this.log(`Current project key: ${userConfig.project}`)
              if (flags.verbose) { // Replace `ProjectsCurrent.flags.verbose` with `flags.verbose`
                  const projects = await fetchProjects(this.token)
                  const currentProject = projects.find((project) => project.key === userConfig.project)
                  if (currentProject) {
                      this.log(`Project Name: ${currentProject.name}`)
                      this.log(`Project Description: ${currentProject.description}`)
                  } else {
                      this.log('Project not found.')
                  }
              }
          } else {
              this.log('No project is currently selected.')
          }
      } catch (error) {
          this.log('Error while loading configuration: ', (error as Error).message)
      }
  }
}
