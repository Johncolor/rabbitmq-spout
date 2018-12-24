# Storm监控实时流处理

## 一、Storm应用描述
根据前端创建监控规则，通过接受kafka的数据，分析不同监控项的规则进行不同的业务逻辑处理。

## 二、开发环境
系统环境 Ubuntu 
开发工具 pycharm/sublime，python2.X
软件环境 storm0.10.X， pyleus

### storm 本地环境搭建
下载storm源码 
>apache-storm-0.10.2

添加环境变量
>sudo vi /etc/profile
source /etc/profile

安装pyleus
>pip install pyleus
>
![1531735019-FlsuNk9ziVoe2H0nYZ116SQqGJyH-jg0?e=3153600000&token=CT86R8zZYVXDyHWEWFoMX4pz0ksOzxtKCaC80si4:xPJzlblcBpLdq3xJjShoz0w9qgo=](http://per.kelantu.com/photos/1531735019-FlsuNk9ziVoe2H0nYZ116SQqGJyH-jg0?e=3153600000&token=CT86R8zZYVXDyHWEWFoMX4pz0ksOzxtKCaC80si4:xPJzlblcBpLdq3xJjShoz0w9qgo=)
```
vim ~/.pyleus.conf

[storm]
# path to Storm executable (pyleus will automatically look in PATH)
#storm_cmd_path: /opt/hadoop/client/storm/bin/storm
storm_cmd_path: /home/lufeng/apache-storm-0.10.2/bin/storm
#storm_cmd_path: /home/lufeng/apache-storm-1.1.1/bin/storm

# optional: use -n option of pyleus CLI instead
nimbus_host: localhost

# java options to pass to Storm CLI
jvm_opts: -Djava.io.tmpdir=/tmp

[build]
# PyPI server to use during the build of your topologies
pypi_index_url: http://pypi.ninjacorp.com/simple/

# always use system-site-packages for pyleus virtualenvs (default: false)
system_site_packages: true

只需要修改storm_cmd_path为自己的路径即可
```
pyleus使用

>使用pyleus编译
pyleus build pyleus_topology.yaml ，之后生成自己的.jar文件，eg：mt_item_topology.jar

>本地测试命令
pyleus local mt_item_topology.jar 

>提交到远程nimbus上
pyleus submit –n nimbus_ip  mt_item_topology.jar

>提交远程之后，可以通过strom ui 查看topology部署情况

## 三、应用
![5b4d95ade4b07df3b43e9af8.png](http://on-img.com/chart_image/5b4d95ade4b07df3b43e9af8.png)
> 上图为storm总业务流程图，以下部分介绍每个bolt的作用与功能

> 数据入口

数据通过配置spout节点，对接kafka数据流
```
- spout:
   name: kafka-float_data
   type: kafka
   parallelism_hint: 3
   options:
      topic: float_data
      zk_hosts: 10.240.3.81:2181,10.240.3.82:2181
      zk_root: /pyleus-kafka-offsets/kafka_float_data
      from_start: false
      binary_data: true
```



> 数据清理

获取数据并对数据去重
float_repeat_filter_bolt.py
通过记录在redis中的dev_key的最新的时间戳来区分哪些进入的数据是已经处理过的数据，并剔除。

查询监控项元数据
float_receive_bolt.py
通过记录在redis中的监控项元数据，来填充每个监控项的其他字段，有sub_dev，max_limit,min_limit,mt_label等

监控项分数处理
float_process_bolt.py
通过对比每个监控项的静态阀值，来计算监控项健康度
计算监控项健康度,用于监控项告警
静态红线：大于静态阀值
静态黄线：静态阀值*0.8 - 静态阀值*1.0
静态正常：小于静态阀值*0.8
静态阀值不存在,100分

> 规则匹配

获取监控项规则
rule_match_bolt.py
通过记录在redis中监控项规则数据，并填充进新数据匹配，规则的数据有，compare_value，compare_time，rule_std，alert_level，over_times等

分配比较时间（目前仅有1m,2m,5m）
1m_rule_bolt.py 2m_rule_bolt.py 5m_rule_bolt.py
每个bolt负责过滤出对应的比较时间的监控项并发送到处理节点


> 规则处理

比较时间处理
1m_calc_bolt.py 2m_calc_bolt.py 5m_calc_bolt.py
接受各自比较时间流进来的数据，对各自的时间窗口做过滤，并把各自比较时间下的数据和比较值做出分组，比较值有 max，min，avg，first等

计算节点
calc_bolt.py
接受比较时间分组后的比较值的数据，根据比较值的方法对数据做出对应的处理，并把值放入每个item的result字段中。

规则判断节点
rule_std_match_bolt.py
根据规则中的判断事件3种判断标准，分别做出对应的判断逻辑（大于等于静态阀值，大于等于静态阀值的80%，不等于静态阀值），判断标准结合比较值对数据做出事件产生。

告警产生
generate_alert_bolt
在每个监控项基础上设置对应的时间窗口，根据事件的产生，对符合连续数据的采集值进入长度窗口中做告警产生，根据规则中设置的连续几次超过阈值后报警的字段来产生告警信息

告警压缩
compress_alert_bolt
通过规则中定义的告警通道沉默时间对告警信息压缩，如果告警通道沉默时间为每5分钟告警一次，则会判断最后一次的告警信息时间对比上一次的告警时间，如果超出告警通道沉默时间则会更新告警信息。

> 数据写入
write_float_es_bolt write_text_es_bolt
将采集到的数据写入float的实时表和历史表

port_status_bolt
将采集到的端口状态，分析出端口的事件并写入到事件库中

dev_monitor_bolt dev_filter_bolt
将当前监控项时间戳与上一次时间戳比较，大于一分钟的记录到设备的id传入消息队列

write_event_bolt
将产生的事件写入到事件库中

data_process（单独为worker部署在外部）
等待消息队列中传输过来的数据，并针对不同的数据做写入数据的操作，目前共有三种写入数据的类型，float_item,text_item,dev_health
前两种直接调用方法写入到不同的es库中
dev_health
根据查询es库中监控项实时表中的数据，统计出每个设备下的健康监控项和异常监控项，再翻译异常原因后写入es中的dev_health表中


## 四、维护
> 计算节点 calc_bolt
```
if tup.values:
  mt_values = tup.values[0]
  results = []
  for method ,datas in mt_values.items():
      if datas:
          if method == 'max':
              result = self.get_max_values(datas)
          elif method == 'min':
              result = self.get_min_values(datas)
          elif method == 'avg':
              result = self.get_avg_values(datas)
          elif method == 'first':
              result = self.get_first_values(datas)
          elif method == 'last':
              result = self.get_last_values(datas)
          elif method == 'per' or method == 'once':
              result = self.get_per_values(datas)
          else:
              # TODO：以后有新的算法，需要扩展该文件
              pass
          if result:
              results.extend(result)
```


> 规则判断节点 rule_match_bolt
```
class StdMatchBolt(SimpleBolt):
    '''
    接收规则匹配的原始数据，逐条进行比较，目前只有3中比较标准（大于等于静态阈值，大于等于静态阈值的80%，不等于静态阈值）
    1、如果没有静态阈值，暂时不产生事件，以后可以根据动态阈值进行比较
    2、如果超过静态阈值，则产生事件
    
    TODO: 暂时将所有的判断标准放在这个文件中执行
        后期需要将标准拆分出来，这个文件只是一个判断标准的总入口，需要将具体的判断分到具体的bolt中
    '''
    OUTPUT_FIELDS = ['items']

    def std_match(self, origin_value, s_threshold, rule_std):
        '''
        判断标准匹配
        '''
        result = False
        if rule_std == 'gte_max_limit':
            result = self.gte_max_limit(origin_value, s_threshold)
        elif rule_std == 'gte_max_limit_80%':
            result = self.gte_80_max_limit(origin_value, s_threshold)
        elif rule_std == 'neq_max_limit':
            result = self.neq_max_limit(origin_value, s_threshold)
        else:
            # TODO
            pass
        return result
```

