from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def show_resource_util():
    cpu_percentage = 100
    memory_percentage = 50
    net_usage = 1000
    data_unit = "MB"

    total_ids=7
    vms_id = list(range(total_ids));
    vms_cpu_usage = [20 for i in range(total_ids)]
    vms_mem_usage = [80 for i in range(total_ids)]
    vms_net_usage = [100 for i in range(total_ids)];

    return render_template('resource_usage.html',avg_cpu_usage=cpu_percentage, mem_usage=memory_percentage,net_usage=net_usage,data_unit=data_unit,vms_id=vms_id, vms_cpu_usage=vms_cpu_usage,vms_mem_usage=vms_mem_usage, vms_net_usage=vms_net_usage,vm_num=len(vms_id))

if __name__ == '__main__':
    app.run()