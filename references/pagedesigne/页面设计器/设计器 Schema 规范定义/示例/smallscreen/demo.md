```json
{
  "schemaVersion": "core-1.0",
  "kind": "page",
  "id": "small-screen-core-example",
  "title": "自然人、法人数量情况",
  "viewport": {
    "width": 390,
    "height": 844,
    "unit": "px",
    "device": "mobile"
  },
  "theme": {
    "background": "#FFFFFF",
    "textColor": "#2E3033",
    "fontFamily": "system"
  },
  "children": [
    {
      "id": "GridContainer_mnzf2vtoph1ljnniiwc",
      "type": "grid",
      "title": "自然人、法人数量情况",
      "style": {
        "marginTop": "16px",
        "marginRight": "16px",
        "marginLeft": "16px",
        "paddingTop": "16px",
        "paddingRight": "16px",
        "paddingBottom": "16px",
        "paddingLeft": "16px",
        "backgroundImage": "linear-gradient(180deg, #E6EFFC 0%, #FFF 13.17%, #FFF 100%)",
        "borderRadius": "8px",
        "boxShadow": "0px 4px 15px 1px rgba(156, 176, 215, 0.15)"
      },
      "gap": 0,
      "columns": [
        {
          "span": 24,
          "children": [
            {
              "id": "GridContainer_mnzf2vto3pplsqx3ef7",
              "type": "grid",
              "title": "一级标题",
              "style": {
                "marginBottom": "16px"
              },
              "gap": 0,
              "columns": [
                {
                  "span": 24,
                  "children": [
                    {
                      "id": "TextComponentM84PD_mnzf2vtovxavm27vsk",
                      "type": "text",
                      "label": "通用文字组件",
                      "text": "数据总览",
                      "style": {
                        "color": "#2E3033",
                        "fontSize": "18px",
                        "lineHeight": "26px",
                        "fontWeight": "700",
                        "textAlign": "left"
                      },
                      "version": "0.1.4",
                      "events": {
                        "mounted": "consoleLog"
                      }
                    }
                  ]
                },
                {
                  "span": 24,
                  "children": [
                    {
                      "id": "GridContainer_mnzf2vtoucxd0g2s1b9",
                      "type": "grid",
                      "title": "网格布局容器",
                      "style": {
                        "paddingTop": "8px"
                      },
                      "gap": 0,
                      "columns": [
                        {
                          "span": 6,
                          "children": [
                            {
                              "id": "LineComponentM84_mnzf2vtohoesvckrcob",
                              "type": "divider",
                              "label": "线组件",
                              "style": {
                                "borderBottomColor": "#3872EA",
                                "borderBottomWidth": "1px",
                                "borderBottomStyle": "solid"
                              },
                              "version": "0.3.5"
                            }
                          ]
                        },
                        {
                          "span": 18,
                          "children": [
                            {
                              "id": "LineComponentM84_mnzf2vtomx14tujhyj",
                              "type": "divider",
                              "label": "线组件",
                              "style": {
                                "borderBottomColor": "#DDE0E4",
                                "borderBottomWidth": "1px",
                                "borderBottomStyle": "solid"
                              },
                              "version": "0.3.5"
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
        },
        {
          "span": 24,
          "children": [
            {
              "id": "GridContainer_mnzf2vto6m6h76y7ky4",
              "type": "grid",
              "title": "网格布局容器",
              "style": {
                "marginBottom": "16px"
              },
              "gap": 0,
              "columns": [
                {
                  "span": 12,
                  "children": [
                    {
                      "id": "GridContainer_mnzf2vtohnkhh3hu5n",
                      "type": "grid",
                      "title": "网格布局容器",
                      "style": {
                        "marginRight": "8px",
                        "paddingTop": "12px",
                        "paddingRight": "12px",
                        "paddingBottom": "12px",
                        "paddingLeft": "12px",
                        "display": "flex",
                        "flexDirection": "row",
                        "alignItems": "flex-end",
                        "justifyContent": "center",
                        "backgroundRepeat": "no-repeat",
                        "backgroundSize": "100% 100%",
                        "backgroundPosition": "center center",
                        "backgroundImage": "url('http://218.4.136.120:8990/smallscreen-demo/smallscreen/data/pid_mo9d8h0ny1nbqi1v7vs/sj11.png')"
                      },
                      "gap": 0,
                      "columns": [
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vtoovos55ji2id",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "实有人口总数",
                              "style": {
                                "paddingBottom": "3px",
                                "color": "#2E3033",
                                "fontSize": "14px",
                                "lineHeight": "21px",
                                "fontWeight": "500",
                                "textAlign": "left"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        },
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vto293towyryei",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "127912",
                              "unit": "人",
                              "style": {
                                "color": "#2E3033",
                                "fontSize": "18px",
                                "lineHeight": "24px",
                                "fontWeight": "700",
                                "textAlign": "left",
                                "overflow": "scroll"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                },
                {
                  "span": 12,
                  "children": [
                    {
                      "id": "GridContainer_mnzf2vto4jnh9i9e25a",
                      "type": "grid",
                      "title": "网格布局容器",
                      "style": {
                        "marginLeft": "8px",
                        "paddingTop": "12px",
                        "paddingRight": "12px",
                        "paddingBottom": "12px",
                        "paddingLeft": "12px",
                        "display": "flex",
                        "flexDirection": "row",
                        "alignItems": "flex-end",
                        "justifyContent": "center",
                        "backgroundImage": "url('http://218.4.136.120:8990/smallscreen-demo/smallscreen/data/pid_mo9d8h0ny1nbqi1v7vs/sj22.png')",
                        "backgroundRepeat": "no-repeat",
                        "backgroundSize": "100% 100%",
                        "backgroundPosition": "center"
                      },
                      "gap": 0,
                      "columns": [
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vtoi3id0clarje",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "特殊人群总数",
                              "style": {
                                "paddingBottom": "3px",
                                "color": "#2E3033",
                                "fontSize": "14px",
                                "lineHeight": "21px",
                                "fontWeight": "500",
                                "textAlign": "left"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        },
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vto4u6jvooq3g2",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "127912",
                              "unit": "人",
                              "style": {
                                "color": "#2E3033",
                                "fontSize": "18px",
                                "lineHeight": "24px",
                                "fontWeight": "700",
                                "textAlign": "left",
                                "overflow": "scroll"
                              },
                              "version": "0.1.4"
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
        },
        {
          "span": 24,
          "children": [
            {
              "id": "GridContainer_mnzf2vtoxzo3ca01069",
              "type": "grid",
              "title": "网格布局容器",
              "style": {},
              "gap": 0,
              "columns": [
                {
                  "span": 12,
                  "children": [
                    {
                      "id": "GridContainer_mnzf2vto6veix9brfpa",
                      "type": "grid",
                      "title": "网格布局容器",
                      "style": {
                        "marginRight": "8px",
                        "paddingTop": "12px",
                        "paddingRight": "12px",
                        "paddingBottom": "12px",
                        "paddingLeft": "12px",
                        "display": "flex",
                        "flexDirection": "row",
                        "alignItems": "flex-end",
                        "justifyContent": "center",
                        "backgroundRepeat": "no-repeat",
                        "backgroundSize": "100% 100%",
                        "backgroundPosition": "center center",
                        "backgroundImage": "url('http://218.4.136.120:8990/smallscreen-demo/smallscreen/data/pid_mo9d8h0ny1nbqi1v7vs/sj33.png')"
                      },
                      "gap": 0,
                      "columns": [
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vto70vykdjipb5",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "房屋楼栋总数",
                              "style": {
                                "paddingBottom": "3px",
                                "color": "#2E3033",
                                "fontSize": "14px",
                                "lineHeight": "21px",
                                "fontWeight": "500",
                                "textAlign": "left"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        },
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vtoq8fucbcixts",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "127912",
                              "unit": "人",
                              "style": {
                                "color": "#2E3033",
                                "fontSize": "18px",
                                "lineHeight": "24px",
                                "fontWeight": "700",
                                "textAlign": "left",
                                "overflow": "scroll"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                },
                {
                  "span": 12,
                  "children": [
                    {
                      "id": "GridContainer_mnzf2vtoeynbdr9erlj",
                      "type": "grid",
                      "title": "网格布局容器",
                      "style": {
                        "marginLeft": "8px",
                        "paddingTop": "12px",
                        "paddingRight": "12px",
                        "paddingBottom": "12px",
                        "paddingLeft": "12px",
                        "display": "flex",
                        "flexDirection": "row",
                        "alignItems": "flex-end",
                        "justifyContent": "center",
                        "backgroundRepeat": "no-repeat",
                        "backgroundSize": "100% 100%",
                        "backgroundPosition": "center center",
                        "backgroundImage": "url('http://218.4.136.120:8990/smallscreen-demo/smallscreen/data/pid_mo9d8h0ny1nbqi1v7vs/sj44.png')"
                      },
                      "gap": 0,
                      "columns": [
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vtoxy400r80a5o",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "组织机构数量",
                              "style": {
                                "paddingBottom": "3px",
                                "color": "#2E3033",
                                "fontSize": "14px",
                                "lineHeight": "21px",
                                "fontWeight": "500",
                                "textAlign": "left"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        },
                        {
                          "span": 24,
                          "children": [
                            {
                              "id": "TextComponentM84PD_mnzf2vtole1gj66f1m",
                              "type": "text",
                              "label": "通用文字组件",
                              "text": "127912",
                              "unit": "人",
                              "style": {
                                "color": "#2E3033",
                                "fontSize": "18px",
                                "lineHeight": "24px",
                                "fontWeight": "700",
                                "textAlign": "left",
                                "overflow": "scroll"
                              },
                              "version": "0.1.4"
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
        },
        {
          "span": 24,
          "children": [
            {
              "id": "GridContainer_econBoard20260421",
              "type": "grid",
              "title": "经济运行看板卡片",
              "style": {
                "marginBottom": "16px",
                "paddingTop": "16px",
                "paddingRight": "16px",
                "paddingBottom": "16px",
                "paddingLeft": "16px",
                "backgroundImage": "linear-gradient(180deg, #E6EFFC 0%, #FFF 13.17%, #FFF 100%)",
                "borderRadius": "8px",
                "boxShadow": "0px 4px 15px 1px rgba(156, 176, 215, 0.15)"
              },
              "gap": 0,
              "columns": [
                {
                  "span": 24,
                  "children": [
                    {
                      "id": "GridContainer_econBoardHeader20260421",
                      "type": "grid",
                      "title": "年度总营收",
                      "style": {
                        "padding": "12px 16px",
                        "marginBottom": "12px",
                        "background": "#FFF8F8",
                        "backgroundImage": "linear-gradient(90deg, #FFF1F1 0%, #FFF8F8 100%)",
                        "borderRadius": "8px",
                        "display": "flex",
                        "flexDirection": "row",
                        "alignItems": "center",
                        "justifyContent": "space-between"
                      },
                      "gap": 0,
                      "columns": [
                        {
                          "span": 12,
                          "children": [
                            {
                              "id": "TextComponentM84PD_econBoardTitle20260421",
                              "type": "text",
                              "label": "标题",
                              "text": "年度总营收",
                              "style": {
                                "color": "#2E3033",
                                "fontSize": "16px",
                                "lineHeight": "24px",
                                "fontWeight": "600",
                                "textAlign": "left"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        },
                        {
                          "span": 12,
                          "children": [
                            {
                              "id": "TextComponentM84PD_econBoardValue20260421",
                              "type": "text",
                              "label": "主数值",
                              "text": "6.28亿",
                              "style": {
                                "color": "#1F2D3D",
                                "fontSize": "28px",
                                "lineHeight": "32px",
                                "fontWeight": "700",
                                "textAlign": "right"
                              },
                              "version": "0.1.4"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                },
                {
                  "span": 24,
                  "children": [
                    {
                      "id": "GridContainer_econBoardQuarterRow20260421",
                      "type": "grid",
                      "title": "季度指标",
                      "gap": 0,
                      "columns": [
                        {
                          "span": 6,
                          "children": [
                            {
                              "id": "GridContainer_econQuarterQ120260421",
                              "type": "grid",
                              "title": "Q1",
                              "style": {
                                "marginRight": "8px",
                                "background": "#F8FAFD",
                                "borderRadius": "4px",
                                "borderWidth": "1px",
                                "borderStyle": "solid",
                                "borderColor": "#E6EBF5",
                                "padding": "12px 8px"
                              },
                              "gap": 0,
                              "columns": [
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ1Title20260421",
                                      "type": "text",
                                      "label": "Q1标题",
                                      "text": "Q1一季度",
                                      "style": {
                                        "marginBottom": "6px",
                                        "color": "#6B7280",
                                        "fontSize": "14px",
                                        "lineHeight": "20px",
                                        "fontWeight": "500",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
                                    }
                                  ]
                                },
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ1Value20260421",
                                      "type": "text",
                                      "label": "Q1数值",
                                      "text": "1.28亿",
                                      "style": {
                                        "color": "#1F2D3D",
                                        "fontSize": "20px",
                                        "lineHeight": "24px",
                                        "fontWeight": "700",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
                                    }
                                  ]
                                }
                              ]
                            }
                          ]
                        },
                        {
                          "span": 6,
                          "children": [
                            {
                              "id": "GridContainer_econQuarterQ220260421",
                              "type": "grid",
                              "title": "Q2",
                              "style": {
                                "marginRight": "8px",
                                "background": "#F8FAFD",
                                "borderRadius": "4px",
                                "borderWidth": "1px",
                                "borderStyle": "solid",
                                "borderColor": "#E6EBF5",
                                "padding": "12px 8px"
                              },
                              "gap": 0,
                              "columns": [
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ2Title20260421",
                                      "type": "text",
                                      "label": "Q2标题",
                                      "text": "Q2二季度",
                                      "style": {
                                        "marginBottom": "6px",
                                        "color": "#6B7280",
                                        "fontSize": "14px",
                                        "lineHeight": "20px",
                                        "fontWeight": "500",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
                                    }
                                  ]
                                },
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ2Value20260421",
                                      "type": "text",
                                      "label": "Q2数值",
                                      "text": "1.45亿",
                                      "style": {
                                        "color": "#1F2D3D",
                                        "fontSize": "20px",
                                        "lineHeight": "24px",
                                        "fontWeight": "700",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
                                    }
                                  ]
                                }
                              ]
                            }
                          ]
                        },
                        {
                          "span": 6,
                          "children": [
                            {
                              "id": "GridContainer_econQuarterQ320260421",
                              "type": "grid",
                              "title": "Q3",
                              "style": {
                                "marginRight": "8px",
                                "background": "#F8FAFD",
                                "borderRadius": "4px",
                                "borderWidth": "1px",
                                "borderStyle": "solid",
                                "borderColor": "#E6EBF5",
                                "padding": "12px 8px"
                              },
                              "gap": 0,
                              "columns": [
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ3Title20260421",
                                      "type": "text",
                                      "label": "Q3标题",
                                      "text": "Q3三季度",
                                      "style": {
                                        "marginBottom": "6px",
                                        "color": "#6B7280",
                                        "fontSize": "14px",
                                        "lineHeight": "20px",
                                        "fontWeight": "500",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
                                    }
                                  ]
                                },
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ3Value20260421",
                                      "type": "text",
                                      "label": "Q3数值",
                                      "text": "1.62亿",
                                      "style": {
                                        "color": "#1F2D3D",
                                        "fontSize": "20px",
                                        "lineHeight": "24px",
                                        "fontWeight": "700",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
                                    }
                                  ]
                                }
                              ]
                            }
                          ]
                        },
                        {
                          "span": 6,
                          "children": [
                            {
                              "id": "GridContainer_econQuarterQ420260421",
                              "type": "grid",
                              "title": "Q4",
                              "style": {
                                "background": "#F8FAFD",
                                "borderRadius": "4px",
                                "borderWidth": "1px",
                                "borderStyle": "solid",
                                "borderColor": "#E6EBF5",
                                "padding": "12px 8px"
                              },
                              "gap": 0,
                              "columns": [
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ4Title20260421",
                                      "type": "text",
                                      "label": "Q4标题",
                                      "text": "Q4四季度",
                                      "style": {
                                        "marginBottom": "6px",
                                        "color": "#6B7280",
                                        "fontSize": "14px",
                                        "lineHeight": "20px",
                                        "fontWeight": "500",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
                                    }
                                  ]
                                },
                                {
                                  "span": 24,
                                  "children": [
                                    {
                                      "id": "TextComponentM84PD_econQuarterQ4Value20260421",
                                      "type": "text",
                                      "label": "Q4数值",
                                      "text": "1.47亿",
                                      "style": {
                                        "color": "#1F2D3D",
                                        "fontSize": "20px",
                                        "lineHeight": "24px",
                                        "fontWeight": "700",
                                        "textAlign": "center"
                                      },
                                      "version": "0.1.4"
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
              ]
            }
          ]
        }
      ]
    }
  ],
  "actions": {
    "saveForm": {
      "steps": [
        {
          "validate": "myntestzb"
        },
        {
          "use": "myntestzbApi.save",
          "body": "model.myntestzb"
        }
      ],
      "onError": {
        "notify": "保存失败",
        "stop": true
      }
    },
    "consoleLog": {
      "steps": [
        {
          "log": "console.log('123123123')"
        }
      ]
    }
  }
}
```