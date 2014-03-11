import numpy as np
import matplotlib.pyplot as plt
import sys

def doMain():
	nodes = np.genfromtxt(sys.argv[1], delimiter = ' ')
	pred_time = np.genfromtxt(sys.argv[2], delimiter = ' ')
	requests = np.genfromtxt(sys.argv[3], delimiter = ' ')

	num_requests = [50]*10
	sigma = 340
	mu = 40
	bins = np.linspace(-420, 500, 200) 
	num_ranges = (1/(sigma * np.sqrt(2 * np.pi)) * np.exp( - (bins - mu)**2 / (2 * sigma**2)))*125000
	num_requests.extend(num_ranges)
	num_requests.extend([50]*10)

	for i in range(len(requests)-1, 0, -1):
		requests[i][1] = requests[i][1] - requests[i-1][1]

	p_times = np.zeros((len(pred_time),2))
	for i in range(len(pred_time)):
		p_times[i] = pred_time[i][:-1]

	n_nodes = []

	for i in range(len(nodes)-1):
		n_nodes.append(nodes[i])
		n_nodes.append(np.array([nodes[i+1][0], nodes[i][1]]))
	n_nodes = np.array(n_nodes)
	#print n_nodes, p_times, requests
	
	## Active requests
	fig, ax1 = plt.subplots()
	ax1.plot(range(len(num_requests)), num_requests, 'b-')
	ax1.set_xlabel('time (s)')
	# Make the y-axis label and tick labels match the line color.
	ax1.set_ylabel('requests/sec', color='b')
	ax1.set_ylim(bottom = 0)
	for tl in ax1.get_yticklabels():
		tl.set_color('b')

	ax2 = ax1.twinx()
	ax2.plot(requests[:,0] - requests[0,0]+5, requests[:,1]/5, 'g-')
	ax2.set_ylabel('requests serviced by LB', color='g')
	for tl in ax2.get_yticklabels():
		tl.set_color('g')
	plt.title('Active Requests')
	plt.show()

	## Number of active Nodes

	fig, ax1 = plt.subplots()
	ax1.plot(range(len(num_requests)), num_requests, 'b-')
	ax1.set_xlabel('time (s)')
	# Make the y-axis label and tick labels match the line color.
	ax1.set_ylabel('requests/sec', color='b')
	for tl in ax1.get_yticklabels():
		tl.set_color('b')
	ax1.set_ylim(bottom = 0)

	ax2 = ax1.twinx()
	ax2.plot(n_nodes[:,0] - requests[0,0]+5, n_nodes[:,1], 'g-')
	ax2.set_ylabel('number of nodes', color='g')
	for tl in ax2.get_yticklabels():
		tl.set_color('g')
	plt.title('Number of active Nodes')
	ax2.set_ylim(bottom = 0)
	plt.show()

	## SLA Violations

	fig, ax1 = plt.subplots()
	ax1.plot(range(len(num_requests)), num_requests, 'b-')
	ax1.set_xlabel('time (s)')
	# Make the y-axis label and tick labels match the line color.
	ax1.set_ylabel('requests/sec', color='b')
	for tl in ax1.get_yticklabels():
		tl.set_color('b')
	sla = 0.5
	SLAs = np.zeros(len(p_times))
	for i in range(len(p_times)):
		SLAs[i] = 1 if p_times[i,1] > sla else 0
	ax2 = ax1.twinx()
	ax2.plot(p_times[:,0] - requests[0,0]+5, SLAs, 'g-')
	ax2.set_ylabel('SLA 0 = satisfied, 1 = violations', color='g')
	for tl in ax2.get_yticklabels():
		tl.set_color('g')
	plt.title('SLA Violations')
	ax1.set_ylim(bottom = 0)
	ax2.set_ylim(-1,2)
	plt.show()

	
if __name__ == '__main__':
	doMain()