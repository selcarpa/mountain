# 用netty实现Trojan

## 完整代码
[selcarpa/surfer tag(1.1-SHAPSHOT)](https://github.com/selcarpa/surfer/releases/tag/1.1-SNAPSHOT)

## 选用技术栈

- kotlin
- Netty
- Trojan

## 什么是Trojan

[Trojan protocol](https://trojan-gfw.github.io/trojan/protocol.html)

## 目标

兼容实现[v2fly/v2fly-core](https://github.com/v2fly/v2ray-core)的ws+tls+trojan配置方式的客户端及服务端

实现http和socks5入口代理，用以在http或者其他客户端中使用此代理

## 介绍

项目采用kotlin语言，它是一种基于JVM的静态类型编程语言，它可以编译成Java字节码，完全兼容Java的生态系统，可以与Java代码无缝互操作。它的语法与Java非常相似，但是它有更多的特性，比如：null安全、扩展函数、运算符重载、lambda表达式、属性代理等等。

Netty是一个异步事件驱动的网络应用程序框架，用于快速开发可维护的高性能协议服务器和客户端。Netty是一个NIO客户端-服务器框架，使用Netty可以快速开发网络应用，例如服务器和客户端协议。Netty提供了一种新的方式来使开发网络应用程序，这种新的方式使得它很容易使用和有很强的扩展性。

## 实现

### 实现http和socks5入栈处理

#### socks5代理

参考:
- [netty/netty example](https://github.com/netty/netty/tree/4.1/example/src/main/java/io/netty/example/socksproxy)
- [socks wiki](https://zh.wikipedia.org/wiki/SOCKS)
- [rfc1928](https://datatracker.ietf.org/doc/html/rfc1928)


由于netty官方的教程实现非常简单，值得注意的时，笔者放弃了socks4的实现，因为大部分客户端已经支持socks5，socks5提供了udp，认证等功能，而socks4稍微有点过时。

##### 入栈处理

初始化通道，在通道建立时，根据Netty的使用方式，我们在管线中加入以下的Handler，用以处理socks5请求。socks5是可选认证的，我们需要在实际的处理handler中，根据配置信息，判断是否需要认证，再进行下一步处理

```kotlin
private fun initSocksInbound(ch: NioSocketChannel, inbound: Inbound) {
    ch.pipeline().addLast(SocksPortUnificationServerHandler()) // socks的协议在netty中官方实现的解码器
    ch.pipeline().addLast(SocksServerHandler(inbound)) // 自定义处理器，用于实际处理socks代理业务
}
```
##### 实际处理代理的部分代码

```kotlin
when (socksRequest) {
    is Socks5InitialRequest -> {
        socks5auth(ctx)
    }

    is Socks5PasswordAuthRequest -> {
        socks5DoAuth(socksRequest, ctx)
    }

    is Socks5CommandRequest -> {
        if (socksRequest.type() === Socks5CommandType.CONNECT) {
            ctx.pipeline().addLast(SocksServerConnectHandler(inbound))
            ctx.pipeline().remove(this)
            ctx.fireChannelRead(socksRequest)
        } else {
            ctx.close()
        }
    }

    else -> {
        ctx.close()
    }
}
/**
 * socks5 auth
 * 初步处理socks5认证
 */
private fun socks5auth(ctx: ChannelHandlerContext) {
    if (inbound.socks5Setting?.auth != null) {
        ctx.pipeline().addFirst(Socks5PasswordAuthRequestDecoder())
        ctx.write(DefaultSocks5InitialResponse(Socks5AuthMethod.PASSWORD))
    } else {
        ctx.pipeline().addFirst(Socks5CommandRequestDecoder())
        ctx.write(DefaultSocks5InitialResponse(Socks5AuthMethod.NO_AUTH))
    }
}

/**
 * socks5 auth
 * 实际处理auth请求
 */
private fun socks5DoAuth(socksRequest: Socks5PasswordAuthRequest, ctx: ChannelHandlerContext) {
    if (inbound.socks5Setting?.auth?.username != socksRequest.username() || inbound.socks5Setting?.auth?.password != socksRequest.password()) {
        logger.warn("socks5 auth failed from: ${ctx.channel().remoteAddress()}")
        ctx.write(DefaultSocks5PasswordAuthResponse(Socks5PasswordAuthStatus.FAILURE))
        ctx.close()
        return
    }
    ctx.pipeline().addFirst(Socks5CommandRequestDecoder())
    ctx.write(DefaultSocks5PasswordAuthResponse(Socks5PasswordAuthStatus.SUCCESS))
}

```

#### http代理

参考:
- [netty/netty example](https://github.com/netty/netty/tree/4.1/example/src/main/java/io/netty/example/proxy)
- [shuaicj/http-proxy-netty](https://github.com/shuaicj/http-proxy-netty)
- [monkeyWie/proxyee](https://github.com/monkeyWie/proxyee)
- [rfc2068](https://datatracker.ietf.org/doc/html/rfc2068#section-8.1.3)

http代理协议实际需要实现两部分，在客户端进行http请求时，只需要转发请求即可，在客户端进行https请求时，服务需要在建立连接后，成为一个中继客户端，透明转发客户端和服务端的数据。

##### 入栈处理

初始化通道，在通道建立时，根据Netty的使用方式，我们在管线中加入以下的Handler，用以处理http请求。

```kotlin
private fun initHttpInbound(ch: NioSocketChannel, inbound: Inbound) {
    ch.pipeline().addLast(
        ChunkedWriteHandler(), // 支持异步发送大的码流，一般用于发送文件流
        HttpServerCodec(), // http服务端编码解码器
        HttpContentCompressor(), // HttpContent 压缩
        HttpObjectAggregator(Int.MAX_VALUE), // http消息聚合器
        HttpProxyServerHandler(inbound)) // 自定义处理器，用于实际处理http代理业务
}

```

实际业务处理handler，区分http和https的代码
```kotlin
override fun channelRead(originCTX: ChannelHandlerContext, msg: Any) {
    //http proxy and http connect method
    //进入handler的请求必定时HttpRequest，使用类型判断隐式类型转换
    if (msg is HttpRequest) {
        //客户端使用代理传输https请求时，会使用CONNECT方法，此时需要建立隧道
        if (msg.method() == HttpMethod.CONNECT) {
            tunnelProxy(originCTX, msg)
        } else { //其余都是http请求
            httpProxy(originCTX, msg)
        }
    }
}
```

### 中继器实现