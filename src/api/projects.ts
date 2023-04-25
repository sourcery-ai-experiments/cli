import axios from 'axios'
import { BASE_URL } from './common'
import { IsNotEmpty, IsOptional, IsString, ValidateNested } from 'class-validator'
import { ProjectSettings } from './projectSettings'

export type Project = {
    id: string
    name: string
    key: string
    description: string
    settings?: ProjectSettings
    color: string
}

export class CreateProjectParams {
    @IsString()
    @IsNotEmpty()
    name: string

    @IsString()
    description: string

    @IsNotEmpty()
    @IsString()
    key: string
}

export class UpdateProjectParams {
    @IsString()
    @IsOptional()
    name?: string;
  
    @IsString()
    @IsOptional()
    key?: string;
  
    @IsString()
    @IsOptional()
    description?: string;
  
    @IsString()
    @IsOptional()
    color?: string;
  
    @ValidateNested()
    @IsOptional()
    settings?: ProjectSettings;
}
  
export const updateProject = async (
    token: string,
    projectKey: string,
    params: UpdateProjectParams
): Promise<Project> => {
    const url = new URL(`/v1/projects/${projectKey}`, BASE_URL)
    const response = await axios.patch(url.href, params, {
        headers: {
            'Content-Type': 'application/json',
            Authorization: token,
        },
    })
  
    return response.data
}

export const fetchProjects = async (token: string): Promise<Project[]> => {
    const url = new URL('/v1/projects', BASE_URL)
    const response = await axios.get(url.href, {
        headers: {
            'Content-Type': 'application/json',
            Authorization: token,
        },
    })

    return response.data
}

export const createProject = async (
    token: string,
    params: CreateProjectParams
): Promise<Project> => {
    const url = new URL('/v1/projects', BASE_URL)
    const response = await axios.post(url.href, params, {
        headers: {
            'Content-Type': 'application/json',
            Authorization: token,
        },
    })

    return response.data
}
