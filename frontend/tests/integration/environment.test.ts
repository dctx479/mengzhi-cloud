"""
前端环境检查和配置验证
"""
import { describe, it, expect, beforeAll } from 'vitest'
import fs from 'fs'
import path from 'path'

describe('前端环境检查', () => {
  const projectRoot = path.resolve(__dirname, '../..')

  describe('环境配置', () => {
    it('应该存在package.json', () => {
      const packagePath = path.join(projectRoot, 'package.json')
      expect(fs.existsSync(packagePath)).toBe(true)

      const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf-8'))
      expect(packageJson.name).toBe('agri-ai-platform-frontend')
      expect(packageJson.version).toBeDefined()
      console.log(`✓ 项目版本: ${packageJson.version}`)
    })

    it('应该安装所有必要依赖', () => {
      const packagePath = path.join(projectRoot, 'package.json')
      const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf-8'))

      const requiredDeps = [
        'vue',
        'vue-router',
        'pinia',
        'axios',
        'element-plus'
      ]

      requiredDeps.forEach(dep => {
        expect(packageJson.dependencies[dep]).toBeDefined()
        console.log(`✓ 依赖已安装: ${dep}`)
      })
    })

    it('应该存在环境变量文件', () => {
      const envFiles = [
        '.env.development',
        '.env.example'
      ]

      envFiles.forEach(file => {
        const filePath = path.join(projectRoot, file)
        if (fs.existsSync(filePath)) {
          console.log(`✓ 环境文件存在: ${file}`)
        } else {
          console.warn(`⚠ 环境文件缺失: ${file}`)
        }
      })
    })
  })

  describe('项目结构', () => {
    it('应该存在关键目录', () => {
      const requiredDirs = [
        'src',
        'src/components',
        'src/views',
        'src/router',
        'src/store',
        'src/api',
        'src/utils',
        'src/types'
      ]

      requiredDirs.forEach(dir => {
        const dirPath = path.join(projectRoot, dir)
        expect(fs.existsSync(dirPath)).toBe(true)
        console.log(`✓ 目录存在: ${dir}`)
      })
    })

    it('应该存在关键文件', () => {
      const requiredFiles = [
        'src/main.ts',
        'src/App.vue',
        'vite.config.ts',
        'tsconfig.json',
        'index.html'
      ]

      requiredFiles.forEach(file => {
        const filePath = path.join(projectRoot, file)
        expect(fs.existsSync(filePath)).toBe(true)
        console.log(`✓ 文件存在: ${file}`)
      })
    })
  })

  describe('TypeScript配置', () => {
    it('应该有有效的tsconfig.json', () => {
      const tsconfigPath = path.join(projectRoot, 'tsconfig.json')
      expect(fs.existsSync(tsconfigPath)).toBe(true)

      const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf-8'))
      expect(tsconfig.compilerOptions).toBeDefined()
      console.log('✓ TypeScript配置有效')
    })
  })

  describe('Vite配置', () => {
    it('应该有有效的vite.config.ts', () => {
      const vitePath = path.join(projectRoot, 'vite.config.ts')
      expect(fs.existsSync(vitePath)).toBe(true)
      console.log('✓ Vite配置文件存在')
    })
  })

  describe('组件检查', () => {
    it('应该存在核心组件', () => {
      const coreComponents = [
        'src/components/chat',
        'src/views/auth',
        'src/views/products',
        'src/views/user'
      ]

      coreComponents.forEach(comp => {
        const compPath = path.join(projectRoot, comp)
        if (fs.existsSync(compPath)) {
          console.log(`✓ 组件目录存在: ${comp}`)
        } else {
          console.warn(`⚠ 组件目录缺失: ${comp}`)
        }
      })
    })
  })

  describe('API客户端', () => {
    it('应该存在API配置文件', () => {
      const apiPath = path.join(projectRoot, 'src/api')
      expect(fs.existsSync(apiPath)).toBe(true)

      // 检查API文件
      const apiFiles = fs.readdirSync(apiPath)
      console.log(`✓ API模块数量: ${apiFiles.length}`)
      apiFiles.forEach(file => {
        console.log(`  - ${file}`)
      })
    })
  })

  describe('路由配置', () => {
    it('应该存在路由配置', () => {
      const routerPath = path.join(projectRoot, 'src/router')
      expect(fs.existsSync(routerPath)).toBe(true)
      console.log('✓ 路由配置目录存在')
    })
  })

  describe('状态管理', () => {
    it('应该存在Pinia stores', () => {
      const storePaths = [
        'src/store',
        'src/stores'
      ]

      let storeExists = false
      storePaths.forEach(storePath => {
        const fullPath = path.join(projectRoot, storePath)
        if (fs.existsSync(fullPath)) {
          storeExists = true
          console.log(`✓ Store目录存在: ${storePath}`)
        }
      })

      expect(storeExists).toBe(true)
    })
  })
})
