```json
{
  "schemaVersion": "core-1.0",
  "kind": "page",
  "id": "sformtestone-page",
  "title": "sform测试1",
  "viewport": {
    "width": 1440,
    "height": 900,
    "unit": "px",
    "device": "desktop"
  },
  "theme": {
    "background": "#FFFFFF",
    "textColor": "#4e5463",
    "fontFamily": "Microsoft Yahei"
  },
  "models": {
    "sformtestone": {
      "type": "record",
      "label": "sform测试1",
      "primaryKey": "rowguid",
      "fields": {
        "xm": {
          "type": "string",
          "label": "姓名",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "xlzd": {
          "type": "string",
          "label": "下拉字段",
          "source": "timezoneOptions",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "xlzd_text": {
          "type": "string",
          "label": "下拉字段文本",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": false
          }
        },
        "bz": {
          "type": "string",
          "label": "备注",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "tenantguid": {
          "type": "string",
          "label": "租户标识",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "operatedate": {
          "type": "date",
          "label": "操作日期",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "operateuserbaseouguid": {
          "type": "string",
          "label": "操作人所在独立部门Guid",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "belongxiaqucode": {
          "type": "string",
          "label": "所属辖区编号",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "rowguid": {
          "type": "string",
          "label": "主键guid",
          "rules": {
            "required": true,
            "readonly": false,
            "submit": true
          }
        },
        "operateuserouguid": {
          "type": "string",
          "label": "操作人所在部门Guid",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "row_id": {
          "type": "number",
          "label": "序号",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "operateusername": {
          "type": "string",
          "label": "操作人姓名",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "yearflag": {
          "type": "string",
          "label": "年份标识",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "operateuserguid": {
          "type": "string",
          "label": "操作人Guid",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        },
        "pviguid": {
          "type": "string",
          "label": "流程标识",
          "rules": {
            "required": false,
            "readonly": false,
            "submit": true
          }
        }
      },
      "initial": {
        "xm": "",
        "xlzd": "",
        "xlzd_text": "",
        "bz": "",
        "tenantguid": "",
        "operatedate": "",
        "operateuserbaseouguid": "",
        "belongxiaqucode": "",
        "rowguid": "",
        "operateuserouguid": "",
        "row_id": null,
        "operateusername": "",
        "yearflag": "",
        "operateuserguid": "",
        "pviguid": ""
      }
    }
  },
  "resources": {
    "timezoneOptions": {
      "type": "dictionary",
      "source": "static",
      "options": [
        {
          "id": "1",
          "text": "(UTC+08:00)北京，澳大利亚，新加坡，香港特别行政区"
        },
        {
          "id": "2",
          "text": "(UTC+08:00)非洲"
        },
        {
          "id": "3",
          "text": "(UTC+08:00)欧美"
        }
      ],
      "map": {
        "label": "text",
        "value": "id"
      }
    },
    "sformtestoneApi": {
      "type": "endpoint",
      "baseUrl": "",
      "operations": {
        "list": {
          "method": "GET",
          "path": "list"
        },
        "save": {
          "method": "POST",
          "path": "save"
        },
        "delete": {
          "method": "DELETE",
          "path": "delete"
        }
      }
    }
  },
  "actions": {
    "initPage": {
      "steps": [
        {
          "function": {
            "name": "onBeforeInitConfig"
          }
        },
        {
          "function": {
            "name": "onAfterInitConfig"
          }
        },
        {
          "function": {
            "name": "onBeforeInitData"
          }
        },
        {
          "run": "refreshSformtestone"
        },
        {
          "function": {
            "name": "onAfterInitData"
          }
        },
        {
          "function": {
            "name": "onPageMounted"
          }
        }
      ],
      "onError": {
        "notify": "页面初始化失败",
        "stop": true
      }
    },
    "refreshSformtestone": {
      "steps": [
        {
          "use": "sformtestoneApi.list",
          "assign": {
            "model.sformtestone": "response"
          }
        }
      ],
      "onError": {
        "notify": "加载表单失败",
        "stop": true
      }
    },
    "saveSformtestone": {
      "steps": [
        {
          "function": {
            "name": "onValidateBefore"
          }
        },
        {
          "validate": "sformtestone"
        },
        {
          "function": {
            "name": "onSaveBefore"
          }
        },
        {
          "use": "sformtestoneApi.save",
          "body": "model.sformtestone"
        },
        {
          "function": {
            "name": "onSaveAfter"
          }
        }
      ],
      "onError": {
        "notify": "保存失败",
        "stop": true
      }
    },
    "deleteSformtestone": {
      "steps": [
        {
          "use": "sformtestoneApi.delete",
          "params": {
            "rowguid": "model.sformtestone.rowguid"
          }
        }
      ],
      "onError": {
        "notify": "删除失败",
        "stop": true
      }
    }
  },
  "events": {
    "load": "initPage"
  },
  "children": [
    {
      "type": "toolbar-vue",
      "id": "ed415a26a-e659-4dcb-a5bd-cd2a1a9126db",
      "props": {
        "label": "vue工具栏_1",
        "position": "top",
        "showButtons": true,
        "showActions": true
      },
      "children": [
        {
          "type": "toolbar-vue-buttons",
          "id": "toolbar-vue-buttons-4orb0ljum",
          "props": {
            "label": "按钮区域"
          },
          "children": [
            {
              "type": "button",
              "id": "e63f5ce0b-94d1-4650-9edc-3f4fba398120",
              "props": {
                "label": "保存"
              },
              "events": {
                "click": "saveSformtestone"
              }
            }
          ]
        },
        {
          "type": "toolbar-vue-actions",
          "id": "toolbar-vue-actions-legacy",
          "props": {
            "label": "操作区域"
          },
          "children": []
        }
      ]
    },
    {
      "type": "form-layout",
      "id": "form-layout-ae7atl5mi",
      "props": {
        "vertical": false,
        "errorMode": "text",
        "showBorder": true,
        "showColon": true
      },
      "children": [
        {
          "type": "form-layout-form",
          "children": [
            {
              "type": "form-row",
              "id": "form-row_84sd2ccr4",
              "props": {
                "inline": false,
                "newSection": false
              },
              "children": [
                {
                  "type": "form-control-wrap",
                  "id": "form-control-wrap-91c5hhcb4",
                  "props": {
                    "span": 6,
                    "label": "姓名"
                  },
                  "children": [
                    {
                      "type": "input",
                      "id": "textbox-267a1u30k",
                      "model": "sformtestone.xm",
                      "props": {
                        "label": "姓名",
                        "placeholder": "请输入姓名",
                        "requiredErrorText": "姓名必填",
                        "maxLength": 50,
                        "showCount": false
                      }
                    }
                  ]
                }
              ]
            },
            {
              "type": "form-row",
              "id": "form-row_2t6430o24",
              "props": {
                "inline": false,
                "newSection": false
              },
              "children": [
                {
                  "type": "form-control-wrap",
                  "id": "form-control-wrap-5n5os0a24",
                  "props": {
                    "span": 6,
                    "label": "下拉字段"
                  },
                  "children": [
                    {
                      "type": "select",
                      "id": "combobox-4dg3uccjt",
                      "model": "sformtestone.xlzd",
                      "textModel": "sformtestone.xlzd_text",
                      "source": "timezoneOptions",
                      "props": {
                        "label": "下拉字段",
                        "placeholder": "请输入下拉字段",
                        "requiredErrorText": "下拉字段必填",
                        "multiSelect": false,
                        "allowInput": true,
                        "showFilter": false,
                        "showClose": true
                      }
                    }
                  ]
                }
              ]
            },
            {
              "type": "form-row",
              "id": "form-row_7a6cb1gul",
              "props": {
                "inline": false,
                "newSection": false
              },
              "children": [
                {
                  "type": "form-control-wrap",
                  "id": "form-control-wrap-7lih1miel",
                  "props": {
                    "span": 6,
                    "label": "备注"
                  },
                  "children": [
                    {
                      "type": "input",
                      "id": "textbox-8btp7iguk",
                      "model": "sformtestone.bz",
                      "props": {
                        "label": "备注",
                        "placeholder": "请输入备注",
                        "requiredErrorText": "备注必填",
                        "maxLength": 50,
                        "showCount": false
                      }
                    }
                  ]
                }
              ]
            },
            {
              "type": "form-row",
              "id": "form-row_9tldcvutt",
              "props": {
                "inline": false,
                "newSection": false
              },
              "children": [
                {
                  "type": "form-control-wrap",
                  "id": "form-control-wrap-2k5dbuldt",
                  "props": {
                    "span": 6,
                    "label": "租户标识"
                  },
                  "children": [
                    {
                      "type": "input",
                      "id": "textbox-31ttrt2r0",
                      "model": "sformtestone.tenantguid",
                      "props": {
                        "label": "租户标识",
                        "placeholder": "请输入租户标识",
                        "requiredErrorText": "租户标识必填",
                        "maxLength": 50,
                        "showCount": false
                      }
                    }
                  ]
                }
              ]
            },
            {
              "type": "form-row",
              "id": "form-row_4ammtk4me",
              "visible": "model.sformtestone.xlzd != '1' || model.sformtestone.xm != 'abc'",
              "props": {
                "inline": false,
                "newSection": false
              },
              "children": [
                {
                  "type": "form-control-wrap",
                  "id": "form-control-wrap-6sgl8486e",
                  "props": {
                    "span": 6,
                    "label": "操作日期"
                  },
                  "children": [
                    {
                      "type": "datepicker",
                      "id": "datepicker-5prem0m2g",
                      "model": "sformtestone.operatedate",
                      "props": {
                        "label": "操作日期",
                        "placeholder": "请输入操作日期",
                        "requiredErrorText": "操作日期必填",
                        "format": "yyyy-MM-dd HH:mm:ss",
                        "allowInput": false
                      }
                    }
                  ]
                }
              ]
            },
            {
              "type": "form-row",
              "id": "form-row_2ocemnki8",
              "props": {
                "inline": false,
                "newSection": false
              },
              "children": [
                {
                  "type": "form-control-wrap",
                  "id": "form-control-wrap-1qbamr0i8",
                  "props": {
                    "span": 6,
                    "label": "操作人所在独立部门Guid"
                  },
                  "children": [
                    {
                      "type": "input",
                      "id": "textbox-854p9fbb8",
                      "model": "sformtestone.operateuserbaseouguid",
                      "props": {
                        "label": "操作人所在独立部门Guid",
                        "placeholder": "请输入操作人所在独立部门Guid",
                        "requiredErrorText": "操作人所在独立部门Guid必填",
                        "maxLength": 50,
                        "showCount": false
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}

```