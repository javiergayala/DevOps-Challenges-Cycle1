#!/usr/bin/env ruby 

require 'rubygems'
require 'bundler/setup'
require 'fog'
require 'progress'

numsvrs = 2
createdServers = Array.new
privateIPs = Array.new
nodes = Array.new
port = 80

def get_input(prompt)
    print "#{prompt}: "
    gets.chomp
end

def get_user
    Fog.credentials[:rackspace_username] || get_input("Username")
end

def get_api
    Fog.credentials[:rackspace_api_key] || get_input("API Key")
end

def get_region
    Fog.credentials[:region] || 'DFW'
end

class CreateServer
    def initialize(connection, svrname, flavor, image)
        @conn = connection
        @svrname = svrname
        @flavor = flavor
        @image = image
    end
    def svrname
        @svrname
    end
    def flavor
        @flavor
    end
    def image
        @image
    end
    def buildit
        @id = @conn.servers.create :name => @svrname,
                                   :flavor_id => @flavor.id,
                                   :image_id => @image.id
        @id.reload
    end
    def id
        @id
    end
end

def lb_create(raxLB, port, privateIPs, nodes)
    lb = raxLB.load_balancers.create :name => 'challenge7-lb',
                                     :protocol => 'HTTP',
                                     :port => port,
                                     :virtual_ips => privateIPs,
                                     :nodes => nodes
    lb.reload
end

# Connect to the Rackspace Cloud
rax = Fog::Compute.new({
    :provider => 'rackspace',
    :rackspace_username => get_user,
    :rackspace_api_key => get_api,
    :version => :v2,
    :rackspace_region => get_region
    })

raxLB = Fog::Rackspace::LoadBalancers.new({
    :rackspace_username => get_user,
    :rackspace_api_key => get_api,
    :rackspace_region => get_region
    })

flavor = rax.flavors.first
image = rax.images.find {|image| image.name =~ /CentOS/}
server_name = get_input("Enter Server Base Name")
svrcount = 0
while svrcount < numsvrs
    this_server = "#{server_name}" + svrcount.to_s
    createdServers[svrcount] = CreateServer.new(rax, this_server, flavor, image)
    createdServers[svrcount].buildit
    svrcount += 1
end
createdServers.each.with_progress('Building Servers') do |svr|
    #puts "Waiting for #{svr.svrname} to be built"
    prog = 0
    Progress.start("#{svr.svrname}", 100) do
        svr.id.wait_for(600, 5) do
            if svr.id.progress > prog
                Progress.step svr.id.progress - prog
                prog = svr.id.progress
            end
            ready?
        end
    end
    privateIPs << Hash["SERVICENET" => svr.id.private_ip_address]
    nodes << Hash["address" => svr.id.private_ip_address,
                  "id" => svr.id.id,
                  "type" => 'PRIMARY',
                  "port" => port,
                  "condition" => 'ENABLED',
                  "weight" => 5]
end

privateIPs.each {|ip| puts "#{ip}"}
nodes.each {|node| puts "#{node}"}

lb_create(raxLB, port, privateIPs, nodes)


